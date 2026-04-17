"""
OmniLocal Orchestrator — Phase Dispatch Nodes.

Each function dispatches a job to the corresponding Phase Worker via HTTP,
then suspends (via LangGraph interrupt) until the Worker fires a webhook.

Design:
    - Orchestrator acts as a "postman" — relays opaque output blobs between phases.
    - global_metadata is attached to every dispatch (all phases need it).
    - source_pdf_path is attached to every dispatch (all phases need it).
    - Phase 1 is special: it PRODUCES global_metadata (extracted and stored separately).
"""

import httpx
from langgraph.types import interrupt

from app.config import DISPATCH_TIMEOUT_SECONDS, PHASE_URLS, WEBHOOK_BASE_URL
from app.state import OmniLocalState
import app.main


async def _dispatch(phase: int, payload: dict) -> None:
    """
    Send a job to a Phase Worker. Returns immediately (Worker processes async).
    """
    url = f"{PHASE_URLS[phase]}/api/v1/phase{phase}/run"
    print(f"[Dispatch] POST {url}")
    async with httpx.AsyncClient(timeout=DISPATCH_TIMEOUT_SECONDS) as client:
        await client.post(url, json=payload)


def _save_dispatch_info(state: dict, phase: int, payload: dict):
    """Save dispatch debug info to in-memory pipelines store."""
    tid = state["thread_id"]
    if tid in app.main._pipelines:
        app.main._pipelines[tid].setdefault("dispatch_info", {})[f"phase_{phase}"] = {
            "url": f"{PHASE_URLS[phase]}/api/v1/phase{phase}/run",
            "payload": payload,
        }


def _extract_result(result, key: str):
    """
    Safely extract a key from the interrupt() resume value.
    LangGraph interrupt() returns the resume value directly.
    Add debug logging to diagnose issues.
    """
    print(f"[Node] interrupt() returned: type={type(result).__name__}, value={result}")
    if isinstance(result, dict):
        return result.get(key, result)
    # Fallback: if result is the value itself (not wrapped in a dict)
    return result


async def call_phase0(state: OmniLocalState) -> dict:
    """Dispatch Phase 0: Demo Edge Detection Worker."""
    payload = {
        "thread_id": state["thread_id"],
        "image_path": state["camera_image_path"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase0",
    }
    _save_dispatch_info(state, 0, payload)
    await _dispatch(0, payload)

    result = interrupt({"waiting_for": "worker_phase0"})
    print(f"[Phase 0] Resume result: {result}")

    return {
        "phase0_results": result,
        "current_phase": 0,
        "status": "COMPLETED",
    }


async def call_phase1(state: OmniLocalState) -> dict:
    """
    Dispatch Phase 1: Ingestion & Structural Parsing.
    Phase 1 PRODUCES global_metadata.
    """
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "brief_path": state["brief_path"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase1",
    }
    _save_dispatch_info(state, 1, payload)
    await _dispatch(1, payload)

    result = interrupt({"waiting_for": "worker_phase1"})
    print(f"[Phase 1] Resume result: {result}")

    output = _extract_result(result, "output_phase_1")

    return {
        "output_phase_1": output,
        "global_metadata": output.get("global_metadata", {}) if isinstance(output, dict) else {},
        "current_phase": 1,
        "status": "COMPLETED",
    }


async def call_phase2(state: OmniLocalState) -> dict:
    """Dispatch Phase 2: Context-Aware Translation."""
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "global_metadata": state["global_metadata"],
        "output_phase_1": state["output_phase_1"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase2",
    }
    _save_dispatch_info(state, 2, payload)
    await _dispatch(2, payload)

    result = interrupt({"waiting_for": "worker_phase2"})
    print(f"[Phase 2] Resume result: {result}")

    output = _extract_result(result, "output_phase_2")

    return {
        "output_phase_2": output,
        "current_phase": 2,
        "status": "COMPLETED",
    }


async def call_phase3(state: OmniLocalState) -> dict:
    """Dispatch Phase 3: Localization & Butterfly Effect."""
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "global_metadata": state["global_metadata"],
        "output_phase_2": state["output_phase_2"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase3",
    }

    if state.get("qa_feedback"):
        payload["qa_feedback"] = state["qa_feedback"]

    _save_dispatch_info(state, 3, payload)
    await _dispatch(3, payload)

    result = interrupt({"waiting_for": "worker_phase3"})
    print(f"[Phase 3] Resume result: {result}")

    output = _extract_result(result, "output_phase_3")

    return {
        "output_phase_3": output,
        "qa_feedback": None,
        "current_phase": 3,
        "status": "COMPLETED",
    }


async def call_phase4(state: OmniLocalState) -> dict:
    """Dispatch Phase 4: Visual Reconstruction & Compositing."""
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "global_metadata": state["global_metadata"],
        "output_phase_3": state["output_phase_3"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase4",
    }
    _save_dispatch_info(state, 4, payload)
    await _dispatch(4, payload)

    result = interrupt({"waiting_for": "worker_phase4"})
    print(f"[Phase 4] Resume result: {result}")

    output = _extract_result(result, "output_phase_4")

    return {
        "output_phase_4": output,
        "current_phase": 4,
        "status": "COMPLETED",
    }


async def call_phase5(state: OmniLocalState) -> dict:
    """Dispatch Phase 5: Quality Assurance."""
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "global_metadata": state["global_metadata"],
        "output_phase_4": state["output_phase_4"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase5",
    }
    _save_dispatch_info(state, 5, payload)
    await _dispatch(5, payload)

    result = interrupt({"waiting_for": "worker_phase5"})
    print(f"[Phase 5] Resume result: {result}")

    qa_status = result.get("qa_status", "APPROVED") if isinstance(result, dict) else "APPROVED"

    update = {
        "qa_status": qa_status,
        "current_phase": 5,
        "status": "COMPLETED",
    }

    if qa_status == "APPROVED":
        update["final_pdf_path"] = result.get("final_pdf_path", "") if isinstance(result, dict) else ""
    else:
        update["qa_feedback"] = result.get("qa_feedback") if isinstance(result, dict) else None
        update["pipeline_iteration"] = state.get("pipeline_iteration", 0) + 1

    return update
