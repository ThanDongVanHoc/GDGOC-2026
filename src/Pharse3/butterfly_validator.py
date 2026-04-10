"""BFS-based Butterfly Effect Validator using Energy Delta.

Implements Task #p3.3 -- validates localization proposals by performing
BFS traversal on the entity graph and computing energy deltas to assess
the risk of cascading semantic conflicts.

Key design decisions:
    - Pure algorithm -- NO LLM calls at validation time.
    - BFS traversal bounded by max_bfs_depth for guaranteed termination.
    - Energy threshold is configurable via config.json.
    - Returns both ACCEPT/REJECT status and detailed energy reasoning.
    - Supports cross-lingual mode using ViAMR-v1.0 Vietnamese corpus.
"""

import logging
from collections import deque
from typing import Any

from .cross_lingual_energy import compute_cross_lingual_delta_energy
from .energy import compute_delta_energy, load_config
from .models import (
    ButterflyConflict,
    LocalizationProposal,
    ValidationResult,
    ValidationStatus,
)

logger = logging.getLogger(__name__)

_CONFIG = load_config()
DEFAULT_ENERGY_THRESHOLD: float = _CONFIG["butterfly_threshold"]
DEFAULT_TOTAL_THRESHOLD: float = _CONFIG["total_energy_threshold"]
MAX_BFS_DEPTH: int = _CONFIG["max_bfs_depth"]


def butterfly_validator(
    proposal: LocalizationProposal,
    entity_graph: dict[str, Any],
    amr_adjacency: dict[str, list[dict[str, str]]] | None = None,
    energy_threshold: float = DEFAULT_ENERGY_THRESHOLD,
    total_energy_threshold: float = DEFAULT_TOTAL_THRESHOLD,
    use_cross_lingual: bool = False,
) -> ValidationResult:
    """Validate a localization proposal using BFS and energy delta.

    Uses a dual-threshold system:
        1. Per-node threshold: flags if any single neighborhood's
           delta energy exceeds energy_threshold.
        2. Total threshold: flags if the cumulative delta energy
           across the entire BFS traversal exceeds
           total_energy_threshold (catches widespread impact).

    This is a pure algorithm — NO LLM calls. Must complete in
    milliseconds for production use.

    Args:
        proposal: The localization proposal (A -> B) to validate.
        entity_graph: The global entity graph from Task #p3.1.
        amr_adjacency: Optional AMR-derived adjacency dict providing
            richer semantic relation types. If None, falls back to
            generic ':related' edges from the entity graph.
        energy_threshold: Per-node delta energy threshold.
            Defaults to the value in config.json.
        total_energy_threshold: Cumulative total delta energy threshold.
            Defaults to the value in config.json.
        use_cross_lingual: If True, uses Vietnamese corpus-aware energy
            computation via ViAMR-v1.0. Requires the ViAMR index to be
            loaded first. Falls back to base energy if unavailable.

    Returns:
        ValidationResult with ACCEPT/REJECT status, total delta energy,
        list of conflicts, and detailed energy edge measurements.
    """
    original = proposal.original
    proposed = proposal.proposed

    # Early exit if entity not in the graph
    if original not in entity_graph:
        logger.warning(
            "Entity '%s' not found in entity graph. Auto-ACCEPT.", original
        )
        return ValidationResult(
            status=ValidationStatus.ACCEPT,
            total_delta_energy=0.0,
            conflicts=[],
            energy_details=[],
        )

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(original, 0)])
    conflicts: list[ButterflyConflict] = []
    all_energy_details = []
    total_delta = 0.0

    while queue:
        current, depth = queue.popleft()

        if current in visited:
            continue
        if depth > MAX_BFS_DEPTH:
            continue

        visited.add(current)

        node = entity_graph.get(current)
        if node is None:
            continue

        # Build neighbor list from entity graph relations
        neighbors: list[dict[str, str]] = []
        for related in node.get("related", []):
            relation = _find_relation(current, related, amr_adjacency)
            neighbors.append({
                "concept": related,
                "relation": relation,
            })

        if not neighbors:
            continue

        # Compute energy delta for this neighborhood
        # Use cross-lingual energy when ViAMR corpus is available
        depth_map = {n["concept"]: depth + 1 for n in neighbors}
        energy_func = (
            compute_cross_lingual_delta_energy
            if use_cross_lingual
            else compute_delta_energy
        )
        delta_e, orig_edges, prop_edges = energy_func(
            original=original,
            proposed=proposed,
            neighbors=neighbors,
            entity_graph=entity_graph,
            depth_map=depth_map,
        )

        total_delta += delta_e
        all_energy_details.extend(orig_edges)

        # Flag as conflict if delta exceeds threshold
        if delta_e > energy_threshold:
            conflict_entities = [n["concept"] for n in neighbors]
            conflict_pages = node.get("pages", [])

            conflicts.append(
                ButterflyConflict(
                    entity=current,
                    pages=conflict_pages,
                    reason=(
                        f"Replacing '{original}' with '{proposed}' causes "
                        f"energy delta {delta_e:.4f} (threshold: "
                        f"{energy_threshold}) at node '{current}' "
                        f"(connected to: {conflict_entities})"
                    ),
                    delta_energy=round(delta_e, 6),
                )
            )

        # Enqueue related entities for further BFS exploration
        for related in node.get("related", []):
            if related not in visited and related in entity_graph:
                queue.append((related, depth + 1))

    # Check total energy threshold (widespread cascade detection)
    if total_delta > total_energy_threshold and not conflicts:
        conflicts.append(
            ButterflyConflict(
                entity=original,
                pages=entity_graph.get(original, {}).get("pages", []),
                reason=(
                    f"Replacing '{original}' with '{proposed}' causes "
                    f"total cumulative energy delta {total_delta:.4f} "
                    f"(threshold: {total_energy_threshold}). "
                    f"The change affects too many connected entities "
                    f"across the narrative."
                ),
                delta_energy=round(total_delta, 6),
            )
        )

    status = (
        ValidationStatus.REJECT if conflicts
        else ValidationStatus.ACCEPT
    )

    result = ValidationResult(
        status=status,
        total_delta_energy=round(total_delta, 6),
        conflicts=conflicts,
        energy_details=all_energy_details,
    )

    logger.info(
        "Validation for '%s' -> '%s': %s (total dE=%.4f, conflicts=%d)",
        original,
        proposed,
        status.value,
        total_delta,
        len(conflicts),
    )

    return result


def _find_relation(
    source: str,
    target: str,
    amr_adjacency: dict[str, list[dict[str, str]]] | None,
) -> str:
    """Find the AMR relation between two concepts.

    Searches the AMR adjacency dict for a direct or inverse edge
    between the source and target. Falls back to ':related' if
    no AMR relation is found.

    Args:
        source: The source concept name.
        target: The target concept name.
        amr_adjacency: The AMR-derived adjacency dict, or None.

    Returns:
        The AMR relation string, or ':related' as fallback.
    """
    if amr_adjacency is None:
        return ":related"

    # Check forward direction
    for neighbor in amr_adjacency.get(source, []):
        if neighbor["concept"] == target:
            return neighbor["relation"]

    # Check reverse direction
    for neighbor in amr_adjacency.get(target, []):
        if neighbor["concept"] == source:
            return neighbor["relation"]

    return ":related"
