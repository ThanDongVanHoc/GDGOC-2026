"""
OmniLocal Orchestrator — Phase Dispatch Nodes.

Each phase is split into two nodes to prevent duplicate dispatches:
    - dispatch_phaseX: Sends job to Worker via HTTP (runs once, completes).
    - wait_phaseX: Suspends via interrupt() until Worker fires webhook.

Why split? LangGraph re-executes the ENTIRE node function when resuming
from an interrupt(). If dispatch + interrupt are in the same function,
the HTTP dispatch fires TWICE (once on initial run, once on resume).
Splitting ensures dispatch runs exactly once.

Design:
    - Orchestrator acts as a "postman" — relays opaque output blobs between phases.
    - global_metadata is attached to every dispatch (all phases need it).
    - source_pdf_path is attached to every dispatch (all phases need it).
    - Phase 1 is special: it PRODUCES global_metadata (extracted and stored separately).
"""

import os
import httpx
from langgraph.types import interrupt

from app.config import DISPATCH_TIMEOUT_SECONDS, PHASE_URLS, WEBHOOK_BASE_URL
from app.state import OmniLocalState
import app.main


async def _dispatch(phase: int, payload: dict) -> None:
    """
    Send a job to a Phase Worker. Returns immediately (Worker processes async).
    """
    # Auto-inject source_pdf_url for remote workers
    if "source_pdf_path" in payload and payload["source_pdf_path"]:
        filename = os.path.basename(payload["source_pdf_path"])
        payload["source_pdf_url"] = f"{WEBHOOK_BASE_URL}/uploads/{filename}"

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


# ═══════════════════════════════════════════════════════════════════
#  PHASE 0 (Demo — kept as single node, runs in separate graph)
# ═══════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════
#  PHASE 1: Ingestion & Structural Parsing
# ═══════════════════════════════════════════════════════════════════

async def dispatch_phase1(state: OmniLocalState) -> dict:
    """Send job to Phase 1 Worker."""
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "brief_path": state["brief_path"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase1",
    }
    _save_dispatch_info(state, 1, payload)
    await _dispatch(1, payload)
    return {"current_phase": 1, "status": "PROCESSING"}


async def wait_phase1(state: OmniLocalState) -> dict:
    """Wait for Phase 1 webhook, then extract results."""
    result = interrupt({"waiting_for": "worker_phase1"})
    print(f"[Phase 1] Resume result: {result}")

    output = _extract_result(result, "output_phase_1")

    return {
        "output_phase_1": output,
        "global_metadata": output.get("global_metadata", {}) if isinstance(output, dict) else {},
        "current_phase": 1,
        "status": "COMPLETED",
    }


# ═══════════════════════════════════════════════════════════════════
#  PHASE 2: Context-Aware Translation
# ═══════════════════════════════════════════════════════════════════

async def dispatch_phase2(state: OmniLocalState) -> dict:
    """Send job to Phase 2 Worker."""
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "global_metadata": state["global_metadata"],
        "output_phase_1": state["output_phase_1"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase2",
    }
    _save_dispatch_info(state, 2, payload)
    await _dispatch(2, payload)
    return {"current_phase": 2, "status": "PROCESSING"}


async def wait_phase2(state: OmniLocalState) -> dict:
    """Wait for Phase 2 webhook, then extract results."""
    result = interrupt({"waiting_for": "worker_phase2"})
    print(f"[Phase 2] Resume result: {result}")

    output = _extract_result(result, "output_phase_2")

    return {
        "output_phase_2": output,
        "current_phase": 2,
        "status": "COMPLETED",
    }


# ═══════════════════════════════════════════════════════════════════
#  PHASE 3: Localization & Butterfly Effect
# ═══════════════════════════════════════════════════════════════════

async def dispatch_phase3(state: OmniLocalState) -> dict:
    """Send job to Phase 3 Worker."""
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
    return {"current_phase": 3, "status": "PROCESSING"}


async def wait_phase3(state: OmniLocalState) -> dict:
    """Wait for Phase 3 webhook, then extract results."""
    result = interrupt({"waiting_for": "worker_phase3"})
    print(f"[Phase 3] Resume result: {result}")

    output = _extract_result(result, "output_phase_3")

    return {
        "output_phase_3": output,
        "qa_feedback": None,
        "current_phase": 3,
        "status": "COMPLETED",
    }


# ═══════════════════════════════════════════════════════════════════
#  PHASE 4: Visual Reconstruction & Compositing
# ═══════════════════════════════════════════════════════════════════

async def dispatch_phase4(state: OmniLocalState) -> dict:
    """Send job to Phase 4 Worker."""
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "global_metadata": state["global_metadata"],
        "output_phase_3": state["output_phase_3"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase4",
    }
    _save_dispatch_info(state, 4, payload)
    await _dispatch(4, payload)
    return {"current_phase": 4, "status": "PROCESSING"}


async def wait_phase4(state: OmniLocalState) -> dict:
    """Wait for Phase 4 webhook, then extract results."""
    result = interrupt({"waiting_for": "worker_phase4"})
    print(f"[Phase 4] Resume result: {result}")

    output = _extract_result(result, "output_phase_4")

    return {
        "output_phase_4": output,
        "current_phase": 4,
        "status": "COMPLETED",
    }


# ═══════════════════════════════════════════════════════════════════
#  PHASE 5: Quality Assurance
# ═══════════════════════════════════════════════════════════════════

async def dispatch_phase5(state: OmniLocalState) -> dict:
    """Send job to Phase 5 Worker (PDF Rebuild + QA)."""
    payload = {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "global_metadata": state["global_metadata"],
        "output_phase_2": state["output_phase_2"],
        "output_phase_3": state["output_phase_3"],
        "output_phase_4": state["output_phase_4"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase5",
    }
    _save_dispatch_info(state, 5, payload)
    await _dispatch(5, payload)
    return {"current_phase": 5, "status": "PROCESSING"}


async def wait_phase5(state: OmniLocalState) -> dict:
    """Wait for Phase 5 webhook, then extract results."""
    result = interrupt({"waiting_for": "worker_phase5"})
    print(f"[Phase 5] Resume result: {result}")

    qa_status = result.get("qa_status", "APPROVED") if isinstance(result, dict) else "APPROVED"

    update = {
        "qa_status": qa_status,
        "current_phase": 5,
        "status": "COMPLETED",
    }

    if qa_status == "APPROVED":
        if "output_phase_5" in result and isinstance(result["output_phase_5"], dict):
            update["final_pdf_path"] = result["output_phase_5"].get("output_pdf_path", "")
        else:
            update["final_pdf_path"] = result.get("final_pdf_path", "") if isinstance(result, dict) else ""
    else:
        update["qa_feedback"] = result.get("qa_feedback") if isinstance(result, dict) else None
        update["pipeline_iteration"] = state.get("pipeline_iteration", 0) + 1

    return update
