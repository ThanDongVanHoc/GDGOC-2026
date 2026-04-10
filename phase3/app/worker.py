"""
OmniLocal — Phase 3 Worker: Cultural Localization & Butterfly Effect.

Your tasks:
    1. Build entity graph (adjacency list) from verified text.
    2. Propose cultural entity replacements.
    3. Validate proposals via BFS/DFS (NO LLM — must be milliseconds).
    4. Apply accepted mutations, log all changes.
    5. Handle qa_feedback if this is a QA-triggered re-run.
"""


async def run(payload: dict) -> dict:
    """
    Main entry point for Phase 3 processing.

    Args:
        payload: Contains verified_text_pack, global_metadata, qa_feedback.

    Returns:
        Dictionary with localized_text_pack and localization_log.
    """
    verified_text_pack = payload["verified_text_pack"]
    global_metadata = payload["global_metadata"]
    qa_feedback = payload.get("qa_feedback")

    # TODO: Implement your logic here
    # If qa_feedback is not None, this is a re-run triggered by QA Phase 5.
    # Use the feedback to fix specific issues.

    localized_text_pack = verified_text_pack  # Placeholder — pass through
    localization_log = []

    return {
        "localized_text_pack": localized_text_pack,
        "localization_log": localization_log,
    }
