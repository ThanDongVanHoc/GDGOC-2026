"""OmniLocal — Phase 3 Worker: Cultural Localization & Butterfly Effect.

Implements the Orchestrator-Worker pattern (see Blueprint_LangGraph.md).
This worker:
    1. Receives verified_text_pack + global_metadata from the Orchestrator.
    2. Builds the entity graph AND loads AMR/ViAMR **in parallel** (Task #p3.1).
    3. Proposes cultural entity replacements via LLM (Task #p3.2).
    4. Filters out proposals that violate locked keywords (global_metadata).
    5. Validates remaining proposals via BFS energy delta (Task #p3.3).
    6. Applies accepted mutations and serializes output (Task #p3.4).
    7. Checks localized text against original bbox capacity; flags overflow.
"""

import asyncio
import copy
import logging
import math
import time
from typing import Any

from core.butterfly_validator import butterfly_validator
from core.entity_graph import build_entity_graph
from core.localization_agent import (
    generate_proposals_fallback,
    generate_proposals_llm,
)
from core.models import LocalizationProposal, ValidationStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Average character width factor (pts) — Vietnamese diacritics tend to be
# slightly wider than Latin, so we use a conservative 0.55 ratio.
_DEFAULT_CHAR_WIDTH_RATIO: float = 0.55

# Vertical line-height multiplier relative to font size.
_LINE_HEIGHT_FACTOR: float = 1.2


# ===================================================================
# Public entry point
# ===================================================================

async def run(payload: dict) -> dict:
    """Main entry point for Phase 3 processing.

    Called by main.py when a job arrives from the Orchestrator.
    Handles both first-run and QA-triggered re-runs.

    Args:
        payload: Contains verified_text_pack, global_metadata, qa_feedback.
            Supports both direct keys and nested output_phase_2 wrapper
            to handle API contract and internal formats.

    Returns:
        Dictionary with output_phase_3 and localization_warnings
        matching the API contract schema.
    """
    # --- Normalize input: handle both API contract and direct formats ---
    if "output_phase_2" in payload:
        phase2 = payload["output_phase_2"]
        verified_text_pack = phase2.get("verified_text_pack", {})
    else:
        verified_text_pack = payload.get("verified_text_pack", {})

    global_metadata = payload.get("global_metadata", {})
    qa_feedback = payload.get("qa_feedback")
    use_llm = payload.get("use_llm", True)

    t_start = time.perf_counter()

    # ==================================================================
    # PARALLEL BLOCK 1: Entity Graph + AMR Enrichment + ViAMR Load
    # Build entity graph, attempt AMR model load, and load ViAMR corpus
    # all at the same time since they are independent.
    # ==================================================================
    logger.info("[Phase3] Starting parallel: entity graph + AMR + ViAMR...")

    entity_graph_coro = asyncio.to_thread(
        build_entity_graph, verified_text_pack
    )
    amr_coro = asyncio.to_thread(
        _try_amr_enrichment, verified_text_pack
    )
    viamr_coro = asyncio.to_thread(_try_viamr_load)

    entity_graph, amr_result, viamr_loaded = await asyncio.gather(
        entity_graph_coro, amr_coro, viamr_coro
    )

    amr_adjacency = amr_result  # May be None if model unavailable

    logger.info(
        "[Phase3] Parallel block 1 done in %.1f ms. "
        "Entities: %d | AMR: %s | ViAMR: %s",
        (time.perf_counter() - t_start) * 1000,
        len(entity_graph),
        "yes" if amr_adjacency else "no",
        "yes" if viamr_loaded else "no",
    )

    # ==================================================================
    # Task #p3.2: Generate proposals (LLM or fallback)
    # ==================================================================
    logger.info("[Phase3] Generating localization proposals...")

    entity_list = _extract_entity_list(verified_text_pack)

    if use_llm:
        proposals = await asyncio.to_thread(
            generate_proposals_llm,
            entity_list,
            global_metadata,
            qa_feedback,
        )
    else:
        protected = global_metadata.get("protected_names", [])
        proposals = generate_proposals_fallback(entity_list, protected)

    logger.info("[Phase3] Proposals generated: %d", len(proposals))

    # ==================================================================
    # Pre-validation: Filter out proposals that touch locked keywords
    # ==================================================================
    allowed_proposals, locked_rejections = _filter_locked_keywords(
        proposals, global_metadata
    )
    logger.info(
        "[Phase3] Locked-keyword filter: %d allowed, %d rejected.",
        len(allowed_proposals),
        len(locked_rejections),
    )

    # ==================================================================
    # Task #p3.3: Validate proposals via Butterfly Effect (parallel)
    # ==================================================================
    logger.info("[Phase3] Validating proposals (parallel)...")

    localization_log: list[dict[str, Any]] = []

    # Add locked rejections to log immediately
    for entry in locked_rejections:
        localization_log.append(entry)

    # Run all validations in parallel using asyncio.gather
    validation_coros = [
        asyncio.to_thread(
            _validate_single_proposal,
            proposal,
            entity_graph,
            amr_adjacency,
            viamr_loaded,
        )
        for proposal in allowed_proposals
    ]
    validation_results = await asyncio.gather(*validation_coros)

    accepted_proposals: list[dict[str, Any]] = []
    rejected_proposals: list[dict[str, Any]] = list(locked_rejections)

    for log_entry in validation_results:
        localization_log.append(log_entry)
        if log_entry["status"] == ValidationStatus.ACCEPT.value:
            accepted_proposals.append(log_entry)
        else:
            rejected_proposals.append(log_entry)

    logger.info(
        "[Phase3] Validation complete: %d accepted, %d rejected.",
        len(accepted_proposals),
        len(rejected_proposals),
    )

    # ==================================================================
    # Task #p3.4: Apply accepted mutations
    # ==================================================================
    localized_text_pack = _apply_mutations(
        verified_text_pack, accepted_proposals
    )

    # --- Post-mutation: Check bbox character-length overflow ---
    overflow_warnings = _check_bbox_overflow(
        original_pack=verified_text_pack,
        localized_pack=localized_text_pack,
    )
    if overflow_warnings:
        logger.warning(
            "[Phase3] %d text blocks exceed original bbox capacity.",
            len(overflow_warnings),
        )

    # --- Serialize into API-contract-compliant output_phase_3 ---
    context_safe_pack, translation_warnings = _serialize_localized_text_pack(
        localized_pack=localized_text_pack,
        original_pack=verified_text_pack,
        overflow_warnings=overflow_warnings,
    )

    # Serialize entity graph — convert EntityNode models to plain dicts
    serialized_entity_graph = {
        name: (node.model_dump() if hasattr(node, "model_dump") else node)
        for name, node in entity_graph.items()
    }

    elapsed_ms = (time.perf_counter() - t_start) * 1000
    logger.info(
        "[Phase3] Pipeline complete in %.1f ms. "
        "%d safe blocks, %d warnings.",
        elapsed_ms,
        len(context_safe_pack),
        len(translation_warnings),
    )

    return {
        "output_phase_3": {
            "context_safe_localized_text_pack": context_safe_pack,
            "entity_graph": serialized_entity_graph,
            "localization_log": localization_log,
        },
        "localization_warnings": translation_warnings,
    }


# ===================================================================
# Parallel helpers
# ===================================================================


def _try_amr_enrichment(
    text_pack: dict,
) -> dict[str, list[dict[str, str]]] | None:
    """Attempt to load AMR model and build AMR adjacency.

    Returns None if amrlib model is not available.

    Args:
        text_pack: The Verified Text Pack.

    Returns:
        AMR adjacency dict or None.
    """
    try:
        from core.amr_parser import load_amr_model
        from core.entity_graph import merge_amr_into_entity_graph

        load_amr_model()

        # Collect all sentences
        sentences = []
        for page in text_pack.get("pages", []):
            for block in page.get("text_blocks", []):
                sentences.append(block.get("text", ""))

        # We only need the adjacency, not to mutate the graph here
        # Build a throwaway graph just for AMR
        from core.entity_graph import build_entity_graph
        temp_graph = build_entity_graph(text_pack)
        adjacency = merge_amr_into_entity_graph(temp_graph, sentences)

        logger.info("[AMR] Enrichment successful: %d concepts.", len(adjacency))
        return adjacency

    except Exception as e:
        logger.info("[AMR] Model not available: %s", e)
        return None


def _try_viamr_load() -> bool:
    """Attempt to load the ViAMR-v1.0 Vietnamese AMR corpus.

    Returns True if loaded successfully, False otherwise.
    """
    try:
        from core.vi_amr_loader import get_index_stats, load_viamr_dataset

        load_viamr_dataset(max_samples=5000)
        stats = get_index_stats()
        logger.info(
            "[ViAMR] Loaded: %d graphs, %d concepts.",
            stats.get("total_graphs", 0),
            stats.get("unique_concepts", 0),
        )
        return True
    except Exception as e:
        logger.info("[ViAMR] Not available: %s", e)
        return False


def _validate_single_proposal(
    proposal: LocalizationProposal,
    entity_graph: dict,
    amr_adjacency: dict | None,
    use_cross_lingual: bool,
) -> dict[str, Any]:
    """Validate a single proposal and return a log entry.

    This function is designed to run in a thread pool for parallel
    validation of multiple proposals.

    Args:
        proposal: The localization proposal to validate.
        entity_graph: The global entity graph.
        amr_adjacency: Optional AMR adjacency dict.
        use_cross_lingual: Whether to use ViAMR-enhanced energy.

    Returns:
        A log entry dict for the localization log.
    """
    result = butterfly_validator(
        proposal=proposal,
        entity_graph=entity_graph,
        amr_adjacency=amr_adjacency,
        use_cross_lingual=use_cross_lingual,
    )

    return {
        "proposal_id": proposal.proposal_id,
        "original": proposal.original,
        "proposed": proposal.proposed,
        "affected_pages": proposal.affected_pages,
        "rationale": proposal.rationale,
        "status": result.status.value,
        "delta_energy": result.total_delta_energy,
        "conflicts": [c.model_dump() for c in result.conflicts],
    }


def _extract_entity_list(text_pack: dict) -> list[dict[str, str]]:
    """Extract a flat list of entities with their page appearances.

    Args:
        text_pack: The Verified Text Pack.

    Returns:
        List of dicts with 'name', 'type', 'pages' keys.
    """
    entity_map: dict[str, dict] = {}

    for page in text_pack.get("pages", []):
        page_id = page.get("page_id", 0)
        for block in page.get("text_blocks", []):
            for ent in block.get("entities", []):
                name = ent.get("name", "")
                if name not in entity_map:
                    entity_map[name] = {
                        "name": name,
                        "type": ent.get("type", "other"),
                        "pages": [],
                    }
                if page_id not in entity_map[name]["pages"]:
                    entity_map[name]["pages"].append(page_id)

    return list(entity_map.values())


# ===================================================================
# Locked-keyword protection
# ===================================================================

def _filter_locked_keywords(
    proposals: list[LocalizationProposal],
    global_metadata: dict,
) -> tuple[list[LocalizationProposal], list[dict[str, Any]]]:
    """Reject proposals that touch globally protected keywords.

    According to CODING_CONVENTION.md §3 and API_CONTRACT.md, the
    ``global_metadata`` contains immutable constraints that MUST be
    enforced at every API boundary:

        - ``protected_names`` (list[str]): Character / entity names
          that must never be renamed or replaced.
        - ``never_change_rules`` (list[str]): Free-text rules that
          encode additional immutability constraints.
        - ``preserve_main_names`` (bool): When True, all entries in
          ``protected_names`` are strictly enforced.
        - ``lock_character_color`` (bool): When True, proposals that
          target colour entities are blocked.

    Args:
        proposals: Candidate proposals from the localization agent.
        global_metadata: The global constraints dict from Phase 1.

    Returns:
        A 2-tuple of (allowed_proposals, rejection_log_entries).
    """
    protected_names: list[str] = global_metadata.get("protected_names", [])
    never_change_rules: list[str] = global_metadata.get("never_change_rules", [])
    preserve_main_names: bool = global_metadata.get("preserve_main_names", True)
    lock_character_color: bool = global_metadata.get("lock_character_color", False)

    # Build a fast lookup set (case-insensitive for safety)
    locked_set: set[str] = set()
    if preserve_main_names:
        locked_set = {name.lower() for name in protected_names}

    allowed: list[LocalizationProposal] = []
    rejected_log: list[dict[str, Any]] = []

    for proposal in proposals:
        rejection_reason = _check_proposal_against_locks(
            proposal=proposal,
            locked_set=locked_set,
            never_change_rules=never_change_rules,
            lock_character_color=lock_character_color,
        )

        if rejection_reason is not None:
            rejected_log.append({
                "proposal_id": proposal.proposal_id,
                "original": proposal.original,
                "proposed": proposal.proposed,
                "affected_pages": proposal.affected_pages,
                "rationale": proposal.rationale,
                "status": "REJECT_LOCKED",
                "delta_energy": 0.0,
                "conflicts": [{
                    "entity": proposal.original,
                    "pages": proposal.affected_pages,
                    "reason": rejection_reason,
                    "delta_energy": 0.0,
                }],
            })
        else:
            allowed.append(proposal)

    return allowed, rejected_log


def _check_proposal_against_locks(
    proposal: LocalizationProposal,
    locked_set: set[str],
    never_change_rules: list[str],
    lock_character_color: bool,
) -> str | None:
    """Return a rejection reason if the proposal violates any lock, else None.

    Args:
        proposal: The localization proposal to check.
        locked_set: Lowered set of protected entity names.
        never_change_rules: Free-text immutability rules.
        lock_character_color: Whether colour-related changes are forbidden.

    Returns:
        A human-readable rejection reason string, or None if safe.
    """
    original_lower = proposal.original.lower()
    proposed_lower = proposal.proposed.lower()

    # 1. Direct match against protected_names
    if original_lower in locked_set:
        return (
            f"Entity '{proposal.original}' is in protected_names and "
            f"must not be renamed."
        )
    if proposed_lower in locked_set:
        return (
            f"Proposed replacement '{proposal.proposed}' collides with "
            f"a protected name and could cause confusion."
        )

    # 2. Check never_change_rules
    for rule in never_change_rules:
        rule_lower = rule.lower()
        if original_lower in rule_lower or proposed_lower in rule_lower:
            return (
                f"Proposal violates never_change_rule: \"{rule}\". "
                f"'{proposal.original}' -> '{proposal.proposed}' is forbidden."
            )

    # 3. Colour-lock guard (heuristic keyword check)
    if lock_character_color:
        _COLOR_KEYWORDS = {
            "red", "blue", "green", "yellow", "black", "white",
            "pink", "purple", "orange", "brown", "grey", "gray",
            "đỏ", "xanh", "vàng", "đen", "trắng", "hồng",
            "tím", "cam", "nâu", "xám",
        }
        original_tokens = set(original_lower.split())
        proposed_tokens = set(proposed_lower.split())
        colour_tokens = original_tokens & _COLOR_KEYWORDS
        if colour_tokens and colour_tokens != (proposed_tokens & _COLOR_KEYWORDS):
            return (
                f"lock_character_color is active — changing colour-related "
                f"terms ({colour_tokens}) is forbidden."
            )

    return None


# ===================================================================
# Bounding-box character-length overflow check
# ===================================================================

def _check_bbox_overflow(
    original_pack: dict,
    localized_pack: dict,
) -> list[dict[str, Any]]:
    """Compare localized text length against original bbox capacity.

    For each text block that was mutated, estimates the maximum number
    of characters the original bounding box can hold.

    Args:
        original_pack: The original Verified Text Pack (before mutation).
        localized_pack: The text pack after accepted mutations are applied.

    Returns:
        A list of warning dicts for blocks that overflow.
    """
    warnings: list[dict[str, Any]] = []

    orig_pages = {
        p.get("page_id"): p for p in original_pack.get("pages", [])
    }

    for page in localized_pack.get("pages", []):
        page_id = page.get("page_id")
        orig_page = orig_pages.get(page_id)
        if orig_page is None:
            continue

        orig_blocks = orig_page.get("text_blocks", [])
        loc_blocks = page.get("text_blocks", [])

        for idx, loc_block in enumerate(loc_blocks):
            if idx >= len(orig_blocks):
                break

            orig_block = orig_blocks[idx]
            orig_text = orig_block.get("content", orig_block.get("text", ""))
            loc_text = loc_block.get("content", loc_block.get("text", ""))

            if orig_text == loc_text:
                continue

            bbox = orig_block.get("bbox", [0, 0, 0, 0])
            font_size = orig_block.get("size", 12.0)
            max_chars = _estimate_bbox_capacity(bbox, font_size)
            actual_chars = len(loc_text)

            if actual_chars > max_chars:
                warnings.append({
                    "page_id": page_id,
                    "block_index": idx,
                    "original_content": orig_text,
                    "localized_content": loc_text,
                    "max_estimated_chars": max_chars,
                    "actual_chars": actual_chars,
                    "bbox": bbox,
                    "overflow_ratio": (
                        round(actual_chars / max_chars, 2)
                        if max_chars > 0 else float("inf")
                    ),
                })

    return warnings


def _estimate_bbox_capacity(
    bbox: list[float],
    font_size: float,
) -> int:
    """Estimate how many characters fit inside a bounding box.

    Args:
        bbox: Bounding box as [x0, y0, x1, y1] in points.
        font_size: The font size in points.

    Returns:
        Estimated maximum number of characters.
    """
    if len(bbox) < 4 or font_size <= 0:
        return 10_000

    x0, y0, x1, y1 = bbox
    box_width = abs(x1 - x0)
    box_height = abs(y1 - y0)

    if box_width <= 0 or box_height <= 0:
        return 10_000

    char_width = font_size * _DEFAULT_CHAR_WIDTH_RATIO
    line_height = font_size * _LINE_HEIGHT_FACTOR

    chars_per_line = math.floor(box_width / char_width)
    num_lines = max(1, math.floor(box_height / line_height))

    return chars_per_line * num_lines


# ===================================================================
# Serialization — flatten into API-contract-compliant format
# ===================================================================

def _serialize_localized_text_pack(
    localized_pack: dict,
    original_pack: dict,
    overflow_warnings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Serialize the internal page-nested text pack into the flat
    ``context_safe_localized_text_pack`` array defined by the Phase 3
    API contract.

    Args:
        localized_pack: The page-nested text pack after mutations.
        original_pack: The original Verified Text Pack (before mutation).
        overflow_warnings: Pre-computed list of overflow warning dicts.

    Returns:
        A 2-tuple of (context_safe_localized_text_pack, localization_warnings).
    """
    overflow_keys: set[tuple[int, int]] = {
        (w["page_id"], w["block_index"]) for w in overflow_warnings
    }

    context_safe_pack: list[dict[str, Any]] = []
    translation_warnings: list[dict[str, Any]] = list(overflow_warnings)

    orig_pages: dict[int, dict] = {
        p.get("page_id"): p for p in original_pack.get("pages", [])
    }

    for page in localized_pack.get("pages", []):
        page_id = page.get("page_id")
        orig_page = orig_pages.get(page_id, {})
        orig_blocks = orig_page.get("text_blocks", [])

        for idx, block in enumerate(page.get("text_blocks", [])):
            if (page_id, idx) in overflow_keys:
                continue

            loc_content = block.get("content", block.get("text", ""))

            if idx < len(orig_blocks):
                orig_block = orig_blocks[idx]
                orig_content = orig_block.get(
                    "content", orig_block.get("text", "")
                )
            else:
                orig_content = loc_content

            context_safe_pack.append({
                "original_content": orig_content,
                "localized_content": loc_content,
                "bbox": block.get("bbox", [0.0, 0.0, 0.0, 0.0]),
                "page_id": page_id,
                "source_type": block.get("source_type", "text"),
                "font": block.get("font", ""),
                "size": block.get("size", 0.0),
                "color": block.get("color", 0),
                "flags": block.get("flags", 0),
                "warning": block.get("warning", None),
            })

    return context_safe_pack, translation_warnings


# ===================================================================
# Task #p3.4 — Mutation application
# ===================================================================

def _apply_mutations(
    text_pack: dict,
    accepted: list[dict[str, Any]],
) -> dict:
    """Apply accepted localization proposals to the text pack.

    Performs find-and-replace on each affected page's text blocks
    for all accepted proposals.

    Args:
        text_pack: The original Verified Text Pack.
        accepted: List of accepted proposal log entries.

    Returns:
        A new text pack dict with mutations applied.
    """
    localized = copy.deepcopy(text_pack)

    for proposal in accepted:
        original = proposal["original"]
        proposed = proposal["proposed"]

        for page in localized.get("pages", []):
            if page.get("page_id") not in proposal.get("affected_pages", []):
                continue
            for block in page.get("text_blocks", []):
                for key in ("content", "text"):
                    if key in block and original in block[key]:
                        block[key] = block[key].replace(original, proposed)

    return localized
