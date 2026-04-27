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
    print(f"\n[Phase 4 API] Received request thread_id={payload.get('thread_id')}", flush=True)
    background_tasks.add_task(_process_and_callback, payload)
    return {"status": "accepted", "thread_id": payload["thread_id"]}


async def _process_and_callback(payload: dict) -> None:
    thread_id = payload["thread_id"]
    webhook_url = payload["webhook_url"]
    print(f"[Phase 4 Worker] Staring task processing for thread {thread_id}...", flush=True)
    try:
        result = await run_worker(payload)
        webhook_body = {"thread_id": thread_id, "result": result, "error": None}
        print(f"[Phase 4 Worker] Processing completed successfully! Firing webhook...", flush=True)
    except Exception as e:
        webhook_body = {"thread_id": thread_id, "result": {}, "error": str(e)}
        print(f"[Phase 4 Worker] Error processing task: {e}", flush=True)
        
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(webhook_url, json=webhook_body)
    print(f"[Phase 4 Worker] Webhook fired to {webhook_url}", flush=True)
