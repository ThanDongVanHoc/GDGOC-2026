"""Energy computation for AMR graph edges.

Defines the Energy function that quantifies semantic coupling strength
between adjacent nodes in an AMR graph. The energy model uses a
multi-factor weighted sum:

    E(u, v) = w_role  × RoleWeight(relation)
            + w_freq  × CoOccurrenceFrequency(u, v)
            + w_depth × DepthPenalty(depth)
            + w_page  × PageSpreadFactor(u, v)

Energy Delta (ΔE) measures the total change in coupling energy when
an entity is substituted, and is the primary signal for butterfly
effect prediction.
"""

import json
import logging
import math
from pathlib import Path
from typing import Any

from .models import EnergyEdge

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration Loading
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict[str, Any]:
    """Load the energy configuration from config.json.

    Returns:
        A dictionary containing energy weights, role mappings,
        thresholds, and normalization constants.

    Raises:
        FileNotFoundError: If config.json is missing.
        json.JSONDecodeError: If config.json is malformed.
    """
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_CONFIG = load_config()

# Energy weight constants from config
W_ROLE: float = _CONFIG["energy_weights"]["role_weight"]
W_FREQ: float = _CONFIG["energy_weights"]["co_occurrence_weight"]
W_DEPTH: float = _CONFIG["energy_weights"]["depth_weight"]
W_PAGE: float = _CONFIG["energy_weights"]["page_spread_weight"]

# AMR relation -> base energy mapping
ROLE_ENERGY_MAP: dict[str, float] = _CONFIG["role_energy_map"]

# Normalization ceilings to keep factors in [0, 1]
MAX_CO_OCCURRENCE: int = _CONFIG["energy_normalization"]["max_co_occurrence"]
MAX_DEPTH: int = _CONFIG["energy_normalization"]["max_depth"]
MAX_PAGE_SPREAD: int = _CONFIG["energy_normalization"]["max_page_spread"]


# ---------------------------------------------------------------------------
# Individual Energy Factor Functions
# ---------------------------------------------------------------------------


def compute_role_weight(relation: str) -> float:
    """Compute the energy contribution from the AMR relation type.

    Core relations like :ARG0 (agent) carry higher weight than
    peripheral ones like :mod (modifier), reflecting the intuition
    that changing a core participant has more downstream impact.

    Args:
        relation: The AMR relation label (e.g., ':ARG0', ':location').

    Returns:
        A float in [0, 1] representing the relation's energy weight.
    """
    # Strip inverse marker (-of) to get the base relation
    base_relation = relation.replace("-of", "")
    return ROLE_ENERGY_MAP.get(
        base_relation, ROLE_ENERGY_MAP.get("default", 0.5)
    )


def compute_co_occurrence_frequency(
    source: str,
    target: str,
    entity_graph: dict[str, dict],
) -> float:
    """Compute normalized co-occurrence frequency between two entities.

    Co-occurrence is measured as the number of pages where both
    entities appear. Higher co-occurrence means tighter coupling —
    changing one entity is more likely to cascade to the other.

    Args:
        source: The source entity name.
        target: The target entity name.
        entity_graph: The global entity graph from Phase 3.1.

    Returns:
        A float in [0, 1] — normalized shared page count.
    """
    source_pages = set(entity_graph.get(source, {}).get("pages", []))
    target_pages = set(entity_graph.get(target, {}).get("pages", []))
    shared_count = len(source_pages & target_pages)
    return min(shared_count / MAX_CO_OCCURRENCE, 1.0)


def compute_depth_penalty(depth: int) -> float:
    """Compute an exponential decay penalty based on graph depth.

    Nodes deeper in the AMR tree are typically modifiers or
    peripheral arguments — they have less global narrative impact.
    Shallower nodes (closer to root) receive higher energy.

    Args:
        depth: The node's depth from the AMR root (0 = root).

    Returns:
        A float in (0, 1] — higher for shallow nodes.
        Returns 0.5 as default if depth is unknown (< 0).
    """
    if depth < 0:
        return 0.5  # Unknown depth fallback
    return math.exp(-0.3 * depth)


def compute_page_spread_factor(
    source: str,
    target: str,
    entity_graph: dict[str, dict],
) -> float:
    """Compute page spread factor for an entity pair.

    Measures how many unique pages the two entities collectively
    span. A wider spread means the localization change would affect
    more of the book, increasing butterfly effect risk.

    Args:
        source: The source entity name.
        target: The target entity name.
        entity_graph: The global entity graph from Phase 3.1.

    Returns:
        A float in [0, 1] — normalized total page coverage.
    """
    source_pages = set(entity_graph.get(source, {}).get("pages", []))
    target_pages = set(entity_graph.get(target, {}).get("pages", []))
    total_unique = len(source_pages | target_pages)
    return min(total_unique / MAX_PAGE_SPREAD, 1.0)


# ---------------------------------------------------------------------------
# Core Energy Computation
# ---------------------------------------------------------------------------


def compute_edge_energy(
    source_concept: str,
    target_concept: str,
    relation: str,
    entity_graph: dict[str, dict],
    depth: int = 0,
) -> EnergyEdge:
    """Compute the coupling energy for a single edge between two concepts.

    Combines four weighted factors into a single energy score:
        E = w_role × RoleWeight + w_freq × CoOcc + w_depth × Depth + w_page × PageSpread

    Args:
        source_concept: The source concept/entity name.
        target_concept: The target concept/entity name.
        relation: The AMR relation type connecting them.
        entity_graph: The global entity graph for page/occurrence data.
        depth: The depth of the edge from the AMR root (default: 0).

    Returns:
        An EnergyEdge object containing the total energy and
        a breakdown of each contributing factor.
    """
    role_w = compute_role_weight(relation)
    co_occ = compute_co_occurrence_frequency(
        source_concept, target_concept, entity_graph
    )
    depth_p = compute_depth_penalty(depth)
    page_s = compute_page_spread_factor(
        source_concept, target_concept, entity_graph
    )

    energy = (
        W_ROLE * role_w
        + W_FREQ * co_occ
        + W_DEPTH * depth_p
        + W_PAGE * page_s
    )

    return EnergyEdge(
        source=source_concept,
        target=target_concept,
        relation=relation,
        energy=round(energy, 6),
        breakdown={
            "role_weight": round(W_ROLE * role_w, 6),
            "co_occurrence": round(W_FREQ * co_occ, 6),
            "depth_penalty": round(W_DEPTH * depth_p, 6),
            "page_spread": round(W_PAGE * page_s, 6),
        },
    )


# ---------------------------------------------------------------------------
# Delta Energy Computation
# ---------------------------------------------------------------------------


def compute_delta_energy(
    original: str,
    proposed: str,
    neighbors: list[dict[str, str]],
    entity_graph: dict[str, dict],
    depth_map: dict[str, int] | None = None,
) -> tuple[float, list[EnergyEdge], list[EnergyEdge]]:
    """Compute the total energy delta when substituting an entity.

    For each neighbor of the original entity, computes the energy
    with the original and proposed replacement, then sums the
    absolute differences. A high ΔE indicates the substitution
    significantly disrupts the semantic coupling landscape.

    Formula:
        ΔE = Σ |E(original, neighbor_i) - E(proposed, neighbor_i)|

    Args:
        original: The original entity being replaced.
        proposed: The proposed replacement entity.
        neighbors: List of neighbor dicts with 'concept' and 'relation'.
        entity_graph: The global entity graph for energy computation.
        depth_map: Optional mapping of neighbor concepts to their
            depths in the AMR graph. Defaults to depth=1 for all.

    Returns:
        A tuple of:
            - total_delta (float): The summed absolute energy delta.
            - original_edges (list[EnergyEdge]): Energy details with original.
            - proposed_edges (list[EnergyEdge]): Energy details with proposed.
    """
    if depth_map is None:
        depth_map = {}

    original_edges: list[EnergyEdge] = []
    proposed_edges: list[EnergyEdge] = []
    total_delta = 0.0

    for neighbor in neighbors:
        neighbor_concept = neighbor["concept"]
        relation = neighbor["relation"]
        depth = depth_map.get(neighbor_concept, 1)

        # Energy with the original entity
        e_original = compute_edge_energy(
            original, neighbor_concept, relation, entity_graph, depth
        )
        original_edges.append(e_original)

        # Energy with the proposed replacement
        e_proposed = compute_edge_energy(
            proposed, neighbor_concept, relation, entity_graph, depth
        )
        proposed_edges.append(e_proposed)

        total_delta += abs(e_original.energy - e_proposed.energy)

    return round(total_delta, 6), original_edges, proposed_edges
