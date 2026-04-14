"""
OmniLocal — Phase 3 Service: Cultural Localization & Butterfly Effect.
"""

import httpx
from fastapi import BackgroundTasks, FastAPI

from app.worker import run as run_worker

app = FastAPI(title="OmniLocal Phase 3 — Localization & Butterfly Effect")


@app.get("/")
async def health() -> dict:
    return {"service": "Phase 3 — Localization", "status": "running"}


@app.post("/api/v1/phase3/run", status_code=202)
async def run_phase(payload: dict, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_process_and_callback, payload)
    return {"status": "accepted", "thread_id": payload["thread_id"]}


async def _process_and_callback(payload: dict) -> None:
    thread_id = payload["thread_id"]
    webhook_url = payload["webhook_url"]
    try:
        result = await run_worker(payload)
        webhook_body = {
            "thread_id": thread_id,
            "output_phase_3": result.get("output_phase_3", {}),
            "localization_warnings": result.get("localization_warnings", []),
            "error": None,
        }
    except Exception as e:
        webhook_body = {
            "thread_id": thread_id,
            "output_phase_3": {},
            "localization_warnings": [],
            "error": str(e),
        }
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(webhook_url, json=webhook_body)
