"""OmniLocal — Phase 3 Worker: Cultural Localization & Butterfly Effect.

Implements the Orchestrator-Worker pattern (see QUICK_START.md).
This worker:
    1. Receives verified_text_pack + global_metadata from the Orchestrator.
    2. Builds the entity graph (Task #p3.1).
    3. Proposes cultural entity replacements (Task #p3.2 — placeholder).
    4. Filters out proposals that violate locked keywords (global_metadata).
    5. Validates remaining proposals via BFS/DFS energy delta (Task #p3.3).
    6. Applies accepted mutations (Task #p3.4).
    7. Checks localized text against original bbox capacity; flags overflow.
"""

import asyncio
import copy
import logging
import math
from typing import Any

from core.butterfly_validator import butterfly_validator
from core.entity_graph import build_entity_graph
from core.models import LocalizationProposal, ValidationStatus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Average character width factor (pts) — used when estimating how many
# characters fit into a bounding box.  Vietnamese diacritics tend to be
# slightly wider than Latin, so we use a conservative 0.55 ratio of
# font-size to mean character width.
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
            - verified_text_pack (dict): JSON from Phase 2 with text + bbox.
            - global_metadata (dict): Global constraints from Phase 1.
            - qa_feedback (dict | None): Feedback from Phase 5 QA on re-run.

    Returns:
        Dictionary with localized_text_pack, localization_log, and
        optional overflow_warnings.
    """
    verified_text_pack = payload["verified_text_pack"]
    global_metadata = payload["global_metadata"]
    qa_feedback = payload.get("qa_feedback")

    # --- Task #p3.1 + #p3.2: Run in parallel ---
    logger.info("[Phase3] Starting entity graph build & proposal generation (parallel)...")
    entity_graph_coro = asyncio.to_thread(
        build_entity_graph, verified_text_pack
    )
    proposals_coro = asyncio.to_thread(
        _generate_proposals, verified_text_pack, global_metadata, qa_feedback
    )
    entity_graph, proposals = await asyncio.gather(
        entity_graph_coro, proposals_coro
    )
    logger.info(
        "[Phase3] Entity graph: %d entities. Proposals: %d generated.",
        len(entity_graph),
        len(proposals),
    )

    # --- Pre-validation: Filter out proposals that touch locked keywords ---
    allowed_proposals, locked_rejections = _filter_locked_keywords(
        proposals, global_metadata
    )
    logger.info(
        "[Phase3] Locked-keyword filter: %d allowed, %d rejected.",
        len(allowed_proposals),
        len(locked_rejections),
    )

    # --- Task #p3.3: Validate allowed proposals via Butterfly Effect ---
    accepted_proposals: list[dict[str, Any]] = []
    rejected_proposals: list[dict[str, Any]] = []
    localization_log: list[dict[str, Any]] = []

    # Append locked rejections to the log immediately
    for entry in locked_rejections:
        localization_log.append(entry)
        rejected_proposals.append(entry)

    for proposal in allowed_proposals:
        result = butterfly_validator(
            proposal=proposal,
            entity_graph=entity_graph,
        )

        log_entry = {
            "proposal_id": proposal.proposal_id,
            "original": proposal.original,
            "proposed": proposal.proposed,
            "affected_pages": proposal.affected_pages,
            "rationale": proposal.rationale,
            "status": result.status.value,
            "delta_energy": result.total_delta_energy,
            "conflicts": [c.model_dump() for c in result.conflicts],
        }
        localization_log.append(log_entry)

        if result.status == ValidationStatus.ACCEPT:
            accepted_proposals.append(log_entry)
        else:
            rejected_proposals.append(log_entry)

    logger.info(
        "[Phase3] Validation complete: %d accepted, %d rejected.",
        len(accepted_proposals),
        len(rejected_proposals),
    )

    # --- Task #p3.4: Apply accepted mutations ---
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
    logger.info(
        "[Phase3] Serialization complete: %d safe blocks, %d warnings.",
        len(context_safe_pack),
        len(translation_warnings),
    )

    # Serialize entity graph — convert EntityNode models to plain dicts
    serialized_entity_graph = {
        name: (node.model_dump() if hasattr(node, "model_dump") else node)
        for name, node in entity_graph.items()
    }

    return {
        "output_phase_3": {
            "context_safe_localized_text_pack": context_safe_pack,
            "entity_graph": serialized_entity_graph,
            "localization_log": localization_log,
        },
        "localization_warnings": translation_warnings,
    }


# ===================================================================
# Task #p3.2 — Proposal generation (placeholder)
# ===================================================================

def _generate_proposals(
    text_pack: dict,
    global_metadata: dict,
    qa_feedback: dict | None,
) -> list[LocalizationProposal]:
    """Generate localization proposals from the verified text pack.

    In the current implementation, returns an empty list (placeholder).
    In production, this would interface with an LLM agent to propose
    culturally appropriate replacements.

    Args:
        text_pack: The Verified Text Pack from Phase 2.
        global_metadata: Global constraints (locked names, etc.).
        qa_feedback: Optional QA feedback for re-run adjustments.

    Returns:
        A list of LocalizationProposal objects.
    """
    # TODO: Implement LLM-driven proposal generation (Task #p3.2)
    # For now, return empty — proposals should come from the
    # localization agent or be passed in the payload.
    return []


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
          encode additional immutability constraints.  Any proposal
          whose ``original`` or ``proposed`` text appears verbatim
          inside a rule string is considered a violation.
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
        A human-readable rejection reason string, or None if the
        proposal is safe.
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

    # 2. Check never_change_rules — reject if the original or proposed
    #    text appears inside any rule string (substring match).
    for rule in never_change_rules:
        rule_lower = rule.lower()
        if original_lower in rule_lower or proposed_lower in rule_lower:
            return (
                f"Proposal violates never_change_rule: \"{rule}\". "
                f"'{proposal.original}' → '{proposal.proposed}' is forbidden."
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
    of characters the original bounding box can hold (using font size
    and box dimensions) and checks whether the localized text exceeds
    that limit.

    The estimation uses:
        max_chars ≈ (box_width / (font_size * char_width_ratio))
                   × (box_height / (font_size * line_height_factor))

    Args:
        original_pack: The original Verified Text Pack (before mutation).
        localized_pack: The text pack after accepted mutations are applied.

    Returns:
        A list of warning dicts for blocks that overflow.  Each dict
        contains page_id, block_index, original_content, localized_content,
        max_estimated_chars, actual_chars, and bbox.
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

            # Skip unchanged blocks
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
                    "overflow_ratio": round(actual_chars / max_chars, 2) if max_chars > 0 else float("inf"),
                })

    return warnings


def _estimate_bbox_capacity(
    bbox: list[float],
    font_size: float,
) -> int:
    """Estimate how many characters fit inside a bounding box.

    Uses a simplified mono-width model:
        chars_per_line = box_width  / (font_size * CHAR_WIDTH_RATIO)
        num_lines      = box_height / (font_size * LINE_HEIGHT_FACTOR)
        capacity       = chars_per_line × num_lines

    Args:
        bbox: Bounding box as [x0, y0, x1, y1] in points.
        font_size: The font size in points.

    Returns:
        Estimated maximum number of characters (integer, floored to
        avoid false positives from rounding).
    """
    if len(bbox) < 4 or font_size <= 0:
        # If bbox or font_size is invalid, return a generous fallback
        # so we don't generate spurious warnings.
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
    API contract (see API_CONTRACT.md §Phase 3).

    Each text block that passed localization safely is emitted as a flat
    dict with keys: original_content, localized_content, bbox, page_id,
    source_type, font, size, color, flags, warning.

    Blocks that overflow their bounding box are **not** included in the
    safe pack; instead they are logged into ``localization_warnings``
    with overflow metadata (page_id, block_index, original_content,
    localized_content, max_estimated_chars, actual_chars, overflow_ratio).

    Args:
        localized_pack: The page-nested text pack after mutations.
        original_pack: The original Verified Text Pack (before mutation).
        overflow_warnings: Pre-computed list of overflow warning dicts
            from ``_check_bbox_overflow``.

    Returns:
        A 2-tuple of (context_safe_localized_text_pack, localization_warnings).
    """
    # Build a fast lookup for overflow blocks: (page_id, block_index)
    overflow_keys: set[tuple[int, int]] = {
        (w["page_id"], w["block_index"]) for w in overflow_warnings
    }

    context_safe_pack: list[dict[str, Any]] = []
    translation_warnings: list[dict[str, Any]] = list(overflow_warnings)

    # Build original content lookup for cross-referencing
    orig_pages: dict[int, dict] = {
        p.get("page_id"): p for p in original_pack.get("pages", [])
    }

    for page in localized_pack.get("pages", []):
        page_id = page.get("page_id")
        orig_page = orig_pages.get(page_id, {})
        orig_blocks = orig_page.get("text_blocks", [])

        for idx, block in enumerate(page.get("text_blocks", [])):
            # If this block overflows, it was already logged — skip
            if (page_id, idx) in overflow_keys:
                continue

            loc_content = block.get("content", block.get("text", ""))

            # Resolve original content from the pre-mutation pack
            if idx < len(orig_blocks):
                orig_block = orig_blocks[idx]
                orig_content = orig_block.get(
                    "content", orig_block.get("text", "")
                )
            else:
                orig_content = loc_content

            # Determine source_type — OCR blocks have a different origin
            source_type = block.get("source_type", "text")

            # Check for any inline warning attached to this block
            warning = block.get("warning", None)

            context_safe_pack.append({
                "original_content": orig_content,
                "localized_content": loc_content,
                "bbox": block.get("bbox", [0.0, 0.0, 0.0, 0.0]),
                "page_id": page_id,
                "source_type": source_type,
                "font": block.get("font", ""),
                "size": block.get("size", 0.0),
                "color": block.get("color", 0),
                "flags": block.get("flags", 0),
                "warning": warning,
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
    for all accepted proposals.  Handles both keying conventions
    ('content' from API contract and 'text' from internal format).

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
                # Support both 'content' (API contract) and 'text' (internal)
                for key in ("content", "text"):
                    if key in block and original in block[key]:
                        block[key] = block[key].replace(original, proposed)

    return localized
