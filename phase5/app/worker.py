"""
OmniLocal — Phase 5 Worker: Quality Assurance & Cross-Phase Feedback.

Your tasks:
    1. Check textual integrity (typos, unnatural line breaks).
    2. Validate Butterfly Effect (cross-check localization_log vs final text).
    3. Validate global constraints (protected names, character colors, bg edits).
    4. Return qa_status + qa_feedback for Orchestrator routing.

    qa_status values:
        "pass"                  → Pipeline ends, export PDF.
        "fail_typo"             → Orchestrator re-runs Phase 3.
        "fail_butterfly"        → Orchestrator re-runs Phase 3.
        "fail_constraint_text"  → Orchestrator re-runs Phase 3.
        "fail_constraint_visual"→ Orchestrator re-runs Phase 4.
"""


async def run(payload: dict) -> dict:
    """
    Main entry point for Phase 5 processing.

    Args:
        payload: Contains composited_pdf_path, global_metadata, localization_log.

    Returns:
        Dictionary with qa_status, qa_feedback, and final_pdf_path.
    """
    composited_pdf_path = payload["composited_pdf_path"]
    global_metadata = payload["global_metadata"]
    localization_log = payload["localization_log"]

    # TODO: Implement your QA checks here
    # issues = []
    # issues += _check_textual_integrity(composited_pdf_path)
    # issues += _check_butterfly(composited_pdf_path, localization_log)
    # issues += _check_constraints(composited_pdf_path, global_metadata)

    # Placeholder: pass everything
    return {
        "qa_status": "pass",
        "qa_feedback": None,
        "final_pdf_path": composited_pdf_path,
    }
