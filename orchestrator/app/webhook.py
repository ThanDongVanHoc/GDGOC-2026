"""
OmniLocal Orchestrator — Webhook Receiver.

Workers call these endpoints when they finish processing.
This resumes the suspended LangGraph node for the corresponding Phase.
"""

import asyncio
from fastapi import APIRouter, BackgroundTasks
from langgraph.types import Command
from app.graph import build_graph, build_demo_graph
from app.db import execute_graph
import app.main

router = APIRouter(prefix="/webhook", tags=["webhook"])

# Lock to prevent duplicate resume attempts per thread
_resume_locks: dict[str, asyncio.Lock] = {}
# Track which phases have been resumed to prevent infinite loops
_resumed_phases: set[str] = set()


async def _resume_pipeline(thread_id: str, phase: int, payload: dict):
    """
    Background task to resume the LangGraph pipeline after a phase completes.
    Includes deduplication lock to prevent infinite retry loops.
    """
    resume_key = f"{thread_id}:phase{phase}"

    # Prevent duplicate resumes
    if resume_key in _resumed_phases:
        print(f"[Orchestrator] Ignoring duplicate webhook for {resume_key}")
        return

    _resumed_phases.add(resume_key)

    state = app.main._pipelines.get(thread_id)
    if not state:
        print(f"Warning: Webhook received for unknown thread: {thread_id}")
        return

    # Acquire per-thread lock to serialize resume calls
    if thread_id not in _resume_locks:
        _resume_locks[thread_id] = asyncio.Lock()

    async with _resume_locks[thread_id]:
        state["current_phase"] = phase
        state["status"] = "PROCESSING"

        try:
            builder = build_demo_graph if phase == 0 else build_graph

            print(f"[Orchestrator] Resuming thread {thread_id} from phase {phase} webhook...")

            # Resume graph — returns the state dict after next interrupt or completion
            final_state = await execute_graph(builder, Command(resume=payload), thread_id)

            if final_state:
                # Sync in-memory tracking with the actual LangGraph state
                state["current_phase"] = final_state.get("current_phase", phase)
                state["status"] = final_state.get("status", "PROCESSING")
                state["qa_status"] = final_state.get("qa_status", "")
                state["final_pdf_path"] = final_state.get("final_pdf_path", "")
                # We intentionally DO NOT overwrite dispatch_info here.
                # Nodes update app.main._pipelines[thread_id]['dispatch_info'] directly before dispatch.
                # final_state['dispatch_info'] might be stale because it's not written back by nodes.

                print(f"[Orchestrator] Graph suspended/completed. current_phase={state['current_phase']}, status={state['status']}")
            else:
                print(f"[Orchestrator] Graph returned None for thread {thread_id}")

        except Exception as e:
            print(f"[Orchestrator] Error resuming thread {thread_id}: {e}")
            import traceback
            traceback.print_exc()
            state["status"] = "ERROR"


@router.post("/phase{phase_id}")
async def receive_webhook(phase_id: int, payload: dict, background_tasks: BackgroundTasks) -> dict:
    """
    Receive results from a Phase Worker.
    """
    thread_id = payload["thread_id"]
    result = payload["result"]

    # Check for duplicate before scheduling
    resume_key = f"{thread_id}:phase{phase_id}"
    if resume_key in _resumed_phases:
        return {"status": "duplicate_ignored", "thread_id": thread_id, "phase": phase_id}

    background_tasks.add_task(_resume_pipeline, thread_id, phase_id, result)

    return {"status": "received", "thread_id": thread_id, "phase": phase_id}
