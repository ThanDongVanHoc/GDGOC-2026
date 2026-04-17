"""
OmniLocal Orchestrator — LangGraph Definition.

The entire pipeline graph: 4 linear edges + 1 conditional edge (QA feedback).
"""

from langgraph.graph import END, StateGraph

from app.nodes import call_phase0, call_phase1, call_phase2, call_phase3, call_phase4, call_phase5
from app.routers import qa_router
from app.state import OmniLocalState


def build_graph(checkpointer=None) -> StateGraph:
    """
    Build the OmniLocal LangGraph state machine.

    Graph structure:
        phase1 → phase2 → phase3 → phase4 → phase5 → qa_router
        qa_router → END              (if APPROVED)
        qa_router → phase3           (if REJECT_LOCALIZATION)
    """
    graph = StateGraph(OmniLocalState)

    # ── Phase Nodes ───────────────────────────────────────────
    graph.add_node("phase1", call_phase1)
    graph.add_node("phase2", call_phase2)
    graph.add_node("phase3", call_phase3)
    graph.add_node("phase4", call_phase4)
    graph.add_node("phase5", call_phase5)

    # ── Linear Pipeline ──────────────────────────────────────
    graph.set_entry_point("phase1")
    graph.add_edge("phase1", "phase2")
    graph.add_edge("phase2", "phase3")
    graph.add_edge("phase3", "phase4")
    graph.add_edge("phase4", "phase5")

    # ── QA Feedback Router (the ONLY conditional edge) ───────
    graph.add_conditional_edges(
        "phase5",
        qa_router,
        {
            "APPROVED": END,
            "REJECT_LOCALIZATION": "phase3",
        },
    )

    return graph.compile(checkpointer=checkpointer)


def build_demo_graph(checkpointer=None) -> StateGraph:
    """
    Standalone graph just for testing Phase 0 (Camera -> Edge Detection loop).
    """
    graph = StateGraph(OmniLocalState)
    graph.add_node("phase0", call_phase0)
    graph.set_entry_point("phase0")
    graph.add_edge("phase0", END)
    
    return graph.compile(checkpointer=checkpointer)
