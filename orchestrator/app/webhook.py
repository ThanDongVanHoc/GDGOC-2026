"""
OmniLocal Orchestrator — Webhook Receiver.

Workers call these endpoints when they finish processing.
This resumes the suspended LangGraph node for the corresponding Phase.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from langgraph.types import Command
from app.graph import build_graph, build_demo_graph
from app.db import execute_graph
import app.main

router = APIRouter(prefix="/webhook", tags=["webhook"])

# In-memory store for graph resumption (replace with persistent store in production)
_pending_results: dict[str, dict] = {}


async def _resume_pipeline(thread_id: str, phase: int, payload: dict):
    """
    Background task to resume the LangGraph pipeline after a phase completes.
    Uses the modern LangGraph Command(resume=...) API.
    """
    state = app.main._pipelines.get(thread_id)
    if not state:
        print(f"Warning: Webhook received for unknown thread: {thread_id}")
        return

    # Update in-memory state tracking
    state["status"] = "PROCESSING"
    
    try:
        if phase == 0:
            builder = build_demo_graph
        else:
            builder = build_graph

        # Resume LangGraph node inside async DB context
        await execute_graph(builder, Command(resume=payload), thread_id)
        
        print(f"[Orchestrator] Successfully resumed thread {thread_id} from phase {phase}")
    except Exception as e:
        print(f"[Orchestrator] Error resuming thread {thread_id}: {e}")
        state["status"] = "ERROR"


@router.post("/phase{phase_id}")
async def receive_webhook(phase_id: int, payload: dict, background_tasks: BackgroundTasks) -> dict:
    """
    Receive results from a Phase Worker.

    The Worker fires this webhook when processing is complete.
    The payload must contain:
        - thread_id: str — matches the pipeline run
        - result: dict — Phase output data

    Args:
        phase_id: The Phase number (1–5).
        payload: Webhook payload from the Worker.

    Returns:
        Acknowledgement response.
    """
    thread_id = payload["thread_id"]
    result = payload["result"]

    # Store result for graph resumption
    _pending_results[f"{thread_id}:phase{phase_id}"] = result

    # Trigger background resumption
    background_tasks.add_task(_resume_pipeline, thread_id, phase_id, result)

    return {"status": "received", "thread_id": thread_id, "phase": phase_id}


def get_pending_result(thread_id: str, phase_id: int) -> dict | None:
    """Retrieve a pending webhook result for graph resumption."""
    key = f"{thread_id}:phase{phase_id}"
    return _pending_results.pop(key, None)
