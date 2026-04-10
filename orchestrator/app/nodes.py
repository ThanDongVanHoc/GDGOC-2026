"""
OmniLocal Orchestrator — Phase Dispatch Nodes.

Each function dispatches a job to the corresponding Phase Worker via HTTP,
then suspends (via LangGraph interrupt) until the Worker fires a webhook.
"""

import httpx
from langgraph.types import interrupt

from app.config import DISPATCH_TIMEOUT_SECONDS, PHASE_URLS, WEBHOOK_BASE_URL
from app.state import OmniLocalState


async def _dispatch(phase: int, payload: dict) -> None:
    """
    Send a job to a Phase Worker. Returns immediately (Worker processes async).

    Args:
        phase: Phase number (1–5).
        payload: JSON payload to send to the Worker.
    """
    url = f"{PHASE_URLS[phase]}/api/v1/phase{phase}/run"
    async with httpx.AsyncClient(timeout=DISPATCH_TIMEOUT_SECONDS) as client:
        await client.post(url, json=payload)


async def call_phase0(state: OmniLocalState) -> dict:
    """Dispatch Phase 0: Demo Edge Detection Worker."""
    await _dispatch(0, {
        "thread_id": state["thread_id"],
        "image_path": state["camera_image_path"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase0",
    })

    result = interrupt({"waiting_for": "worker_phase0"})

    return {
        "phase0_results": result,
        "current_phase": 0,
        "status": "COMPLETED",
    }


async def call_phase1(state: OmniLocalState) -> dict:
    """Dispatch Phase 1: Ingestion & Structural Parsing."""
    await _dispatch(1, {
        "thread_id": state["thread_id"],
        "source_pdf_path": state["source_pdf_path"],
        "brief_path": state["brief_path"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase1",
    })

    result = interrupt({"waiting_for": "worker_phase1"})

    return {
        "global_metadata": result["global_metadata"],
        "standardized_pack": result["standardized_pack"],
        "current_phase": 1,
        "status": "COMPLETED",
    }


async def call_phase2(state: OmniLocalState) -> dict:
    """Dispatch Phase 2: Constrained Translation & Review."""
    await _dispatch(2, {
        "thread_id": state["thread_id"],
        "standardized_pack": state["standardized_pack"],
        "global_metadata": state["global_metadata"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase2",
    })

    result = interrupt({"waiting_for": "worker_phase2"})

    return {
        "verified_text_pack": result["verified_text_pack"],
        "translation_warnings": result.get("translation_warnings", []),
        "current_phase": 2,
        "status": "COMPLETED",
    }


async def call_phase3(state: OmniLocalState) -> dict:
    """Dispatch Phase 3: Cultural Localization & Butterfly Effect."""
    await _dispatch(3, {
        "thread_id": state["thread_id"],
        "verified_text_pack": state["verified_text_pack"],
        "global_metadata": state["global_metadata"],
        "qa_feedback": state.get("qa_feedback"),
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase3",
    })

    result = interrupt({"waiting_for": "worker_phase3"})

    return {
        "localized_text_pack": result["localized_text_pack"],
        "localization_log": result["localization_log"],
        "qa_feedback": None,  # Clear after consumption
        "current_phase": 3,
        "status": "COMPLETED",
    }


async def call_phase4(state: OmniLocalState) -> dict:
    """Dispatch Phase 4: Visual Reconstruction & Compositing."""
    await _dispatch(4, {
        "thread_id": state["thread_id"],
        "localized_text_pack": state["localized_text_pack"],
        "localization_log": state["localization_log"],
        "source_pdf_path": state["source_pdf_path"],
        "global_metadata": state["global_metadata"],
        "qa_feedback": state.get("qa_feedback"),
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase4",
    })

    result = interrupt({"waiting_for": "worker_phase4"})

    return {
        "composited_pdf_path": result["composited_pdf_path"],
        "qa_feedback": None,  # Clear after consumption
        "current_phase": 4,
        "status": "COMPLETED",
    }


async def call_phase5(state: OmniLocalState) -> dict:
    """Dispatch Phase 5: Quality Assurance."""
    await _dispatch(5, {
        "thread_id": state["thread_id"],
        "composited_pdf_path": state["composited_pdf_path"],
        "global_metadata": state["global_metadata"],
        "localization_log": state["localization_log"],
        "webhook_url": f"{WEBHOOK_BASE_URL}/webhook/phase5",
    })

    result = interrupt({"waiting_for": "worker_phase5"})

    update = {
        "qa_status": result["qa_status"],
        "current_phase": 5,
        "status": "COMPLETED",
    }

    if result["qa_status"] == "pass":
        update["final_pdf_path"] = result["final_pdf_path"]
    else:
        update["qa_feedback"] = result["qa_feedback"]
        update["pipeline_iteration"] = state.get("pipeline_iteration", 0) + 1

    return update
