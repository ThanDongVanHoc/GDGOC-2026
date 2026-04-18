"""
OmniLocal — Phase 1 Service: Ingestion & Structural Parsing.

FastAPI entry point. Receives job from Orchestrator, processes in background,
fires webhook when complete.
"""

import httpx
from fastapi import BackgroundTasks, FastAPI

from app.worker_remote import run as run_worker

app = FastAPI(title="OmniLocal Phase 1 — Ingestion & Structural Parsing")


@app.get("/")
async def health() -> dict:
    """Health check."""
    return {"service": "Phase 1 — Ingestion", "status": "running"}


@app.post("/api/v1/phase1/run", status_code=202)
async def run_phase(payload: dict, background_tasks: BackgroundTasks) -> dict:
    """
    Receive a job from the Orchestrator.

    Returns 202 immediately, then processes in background.
    Fires webhook when processing is complete.
    """
    background_tasks.add_task(_process_and_callback, payload)
    return {"status": "accepted", "thread_id": payload["thread_id"]}


async def _process_and_callback(payload: dict) -> None:
    """Run worker logic and fire webhook with results."""
    thread_id = payload["thread_id"]
    webhook_url = payload["webhook_url"]

    try:
        result = await run_worker(payload)
        webhook_payload = {"thread_id": thread_id, "result": result, "error": None}
    except Exception as e:
        webhook_payload = {"thread_id": thread_id, "result": {}, "error": str(e)}

    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(webhook_url, json=webhook_payload)
