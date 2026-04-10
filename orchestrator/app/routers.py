"""
OmniLocal Orchestrator — QA Router.

The only routing decision in the Orchestrator.
Reads qa_status from Phase 5 and routes to the appropriate Phase or END.
"""

from app.config import MAX_PIPELINE_ITERATIONS
from app.state import OmniLocalState


def qa_router(state: OmniLocalState) -> str:
    """
    Route based on Phase 5 QA result.

    Args:
        state: Current pipeline state containing qa_status.

    Returns:
        Routing key: "pass", "fail_typo", "fail_butterfly",
        "fail_constraint_text", or "fail_constraint_visual".
    """
    iteration = state.get("pipeline_iteration", 0)

    # Safety: prevent infinite feedback loops
    if iteration >= MAX_PIPELINE_ITERATIONS and state["qa_status"] != "pass":
        return "pass"

    return state["qa_status"]
