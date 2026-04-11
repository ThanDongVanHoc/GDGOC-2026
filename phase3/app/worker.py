"""OmniLocal — Phase 3 Worker: Cultural Localization & Butterfly Effect.

Implements the Orchestrator-Worker pattern (see QUICK_START.md).
This worker:
    1. Receives verified_text_pack + global_metadata from the Orchestrator.
    2. Builds the entity graph (Task #p3.1).
    3. Proposes cultural entity replacements (Task #p3.2 — placeholder).
    4. Validates proposals via BFS/DFS energy delta (Task #p3.3).
    5. Applies accepted mutations and returns the results (Task #p3.4).
"""

import logging
from typing import Any

from core.butterfly_validator import butterfly_validator
from core.entity_graph import build_entity_graph
from core.models import LocalizationProposal, ValidationStatus

logger = logging.getLogger(__name__)


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
        Dictionary with localized_text_pack and localization_log.
    """
    verified_text_pack = payload["verified_text_pack"]
    global_metadata = payload["global_metadata"]
    qa_feedback = payload.get("qa_feedback")

    logger.info("[Phase3] Building entity graph (Task #p3.1)...")
    entity_graph = build_entity_graph(verified_text_pack)
    logger.info(
        "[Phase3] Entity graph built: %d entities.", len(entity_graph)
    )

    # --- Task #p3.2: Generate localization proposals ---
    # In production, this would be driven by an LLM agent that scans
    # the verified text for Western cultural entities and proposes
    # Vietnamese equivalents respecting global_metadata constraints.
    proposals = _generate_proposals(
        verified_text_pack, global_metadata, qa_feedback
    )
    logger.info(
        "[Phase3] Generated %d localization proposals.", len(proposals)
    )

    # --- Task #p3.3: Validate proposals via Butterfly Effect ---
    accepted_proposals: list[dict[str, Any]] = []
    rejected_proposals: list[dict[str, Any]] = []
    localization_log: list[dict[str, Any]] = []

    for proposal in proposals:
        result = butterfly_validator(
            proposal=proposal,
            entity_graph=entity_graph,
        )

        log_entry = {
            "proposal_id": proposal.proposal_id,
            "original": proposal.original,
            "proposed": proposal.proposed,
            "affected_pages": proposal.affected_pages,
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

    return {
        "localized_text_pack": localized_text_pack,
        "localization_log": localization_log,
    }


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
    import copy

    localized = copy.deepcopy(text_pack)

    for proposal in accepted:
        original = proposal["original"]
        proposed = proposal["proposed"]

        for page in localized.get("pages", []):
            if page.get("page_id") not in proposal.get("affected_pages", []):
                continue
            for block in page.get("text_blocks", []):
                if original in block.get("text", ""):
                    block["text"] = block["text"].replace(original, proposed)

    return localized
