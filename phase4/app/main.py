"""
OmniLocal — Phase 4 Service: Visual Reconstruction & Compositing.
"""

import httpx
from fastapi import BackgroundTasks, FastAPI

from app.worker import run as run_worker

app = FastAPI(title="OmniLocal Phase 4 — Visual Reconstruction & Compositing")


@app.get("/")
async def health() -> dict:
    return {"service": "Phase 4 — Compositing", "status": "running"}


@app.post("/api/v1/phase4/run", status_code=202)
async def run_phase(payload: dict, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_process_and_callback, payload)
    return {"status": "accepted", "thread_id": payload["thread_id"]}


async def _process_and_callback(payload: dict) -> None:
    thread_id = payload["thread_id"]
    webhook_url = payload["webhook_url"]
    try:
        result = await run_worker(payload)
        webhook_body = {"thread_id": thread_id, "result": result, "error": None}
    except Exception as e:
        webhook_body = {"thread_id": thread_id, "result": {}, "error": str(e)}
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(webhook_url, json=webhook_body)
