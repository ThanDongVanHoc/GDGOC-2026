"""
OmniLocal Orchestrator — LangGraph Definition.

The entire pipeline graph: dispatch/wait node pairs + 1 conditional edge (QA feedback).

Each phase is split into dispatch (HTTP send) and wait (interrupt) nodes
to prevent LangGraph's resume mechanism from re-firing HTTP dispatches.
"""

from langgraph.graph import END, StateGraph

from app.nodes import (
    call_phase0,
    dispatch_phase1, wait_phase1,
    dispatch_phase2, wait_phase2,
    dispatch_phase3, wait_phase3,
    dispatch_phase4, wait_phase4,
    dispatch_phase5, wait_phase5,
)
from app.routers import qa_router
from app.state import OmniLocalState


def build_graph(checkpointer=None) -> StateGraph:
    """
    Build the OmniLocal LangGraph state machine.

    Graph structure:
        dispatch1 → wait1 → dispatch2 → wait2 → dispatch3 → wait3
        → dispatch4 → wait4 → dispatch5 → wait5 → qa_router
        qa_router → END                  (if APPROVED)
        qa_router → dispatch_phase3      (if REJECT_LOCALIZATION)
    """
    graph = StateGraph(OmniLocalState)

    # ── Phase Nodes (dispatch + wait pairs) ──────────────────
    graph.add_node("dispatch_phase1", dispatch_phase1)
    graph.add_node("wait_phase1", wait_phase1)
    graph.add_node("dispatch_phase2", dispatch_phase2)
    graph.add_node("wait_phase2", wait_phase2)
    graph.add_node("dispatch_phase3", dispatch_phase3)
    graph.add_node("wait_phase3", wait_phase3)
    graph.add_node("dispatch_phase4", dispatch_phase4)
    graph.add_node("wait_phase4", wait_phase4)
    graph.add_node("dispatch_phase5", dispatch_phase5)
    graph.add_node("wait_phase5", wait_phase5)

    # ── Linear Pipeline ──────────────────────────────────────
    graph.set_entry_point("dispatch_phase1")
    graph.add_edge("dispatch_phase1", "wait_phase1")
    graph.add_edge("wait_phase1", "dispatch_phase2")
    graph.add_edge("dispatch_phase2", "wait_phase2")
    graph.add_edge("wait_phase2", "dispatch_phase3")
    graph.add_edge("dispatch_phase3", "wait_phase3")
    graph.add_edge("wait_phase3", "dispatch_phase4")
    graph.add_edge("dispatch_phase4", "wait_phase4")
    graph.add_edge("wait_phase4", "dispatch_phase5")
    graph.add_edge("dispatch_phase5", "wait_phase5")

    # ── QA Feedback Router (the ONLY conditional edge) ───────
    graph.add_conditional_edges(
        "wait_phase5",
        qa_router,
        {
            "APPROVED": END,
            "REJECT_LOCALIZATION": "dispatch_phase3",
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
