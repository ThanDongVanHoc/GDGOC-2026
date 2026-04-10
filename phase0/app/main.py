"""
Phase 0 — Example FastAPI Service.

=== THIS IS AN EXAMPLE FOR PARTNERS TO STUDY ===

This file handles:
    1. Receiving a job from the Orchestrator (POST endpoint)
    2. Returning 202 Accepted immediately
    3. Running worker.py in the background
    4. Firing a webhook when processing is complete

You should NOT need to modify this file much for your own Phase.
Just change the endpoint path and the app title.
"""

import httpx
from fastapi import BackgroundTasks, FastAPI

from app.worker import run as run_worker

app = FastAPI(
    title="OmniLocal Phase 0 — Example Worker (Edge Detection)",
    description="A working example demonstrating the Orchestrator-Worker-Webhook pattern.",
)


@app.get("/")
async def health() -> dict:
    """Health check — the Orchestrator may ping this to verify your service is up."""
    return {"service": "Phase 0 — Example (Edge Detection)", "status": "running"}


@app.post("/api/v1/phase0/run", status_code=202)
async def run_phase(payload: dict, background_tasks: BackgroundTasks) -> dict:
    """
    Receive a job from the Orchestrator.

    IMPORTANT: Return 202 immediately. Do NOT block here.
    The actual processing happens in the background.

    The payload contains:
        - thread_id: str — unique pipeline run ID
        - image_path: str — path to input image
        - webhook_url: str — URL to POST results back to

    Returns:
        202 Accepted with thread_id confirmation.
    """
    print(f"[Phase0] Job received: thread_id={payload['thread_id']}")

    # Schedule heavy work in background — this returns immediately
    background_tasks.add_task(_process_and_callback, payload)

    return {"status": "accepted", "thread_id": payload["thread_id"]}


async def _process_and_callback(payload: dict) -> None:
    """
    Background task: run the worker, then fire webhook.

    This is the glue between your endpoint and your worker.
    You probably don't need to change this for your Phase.
    """
    thread_id = payload["thread_id"]
    webhook_url = payload["webhook_url"]

    try:
        # ── Run your worker logic ────────────────────────────────
        result = await run_worker(payload)

        # ── Success: build webhook payload ───────────────────────
        webhook_payload = {
            "thread_id": thread_id,
            "result": result,
            "error": None,
        }
        print(f"[Phase0] Processing complete. Firing webhook to {webhook_url}")

    except Exception as e:
        # ── Error: still fire webhook so Orchestrator doesn't hang ─
        webhook_payload = {
            "thread_id": thread_id,
            "result": {},
            "error": str(e),
        }
        print(f"[Phase0] Processing FAILED: {e}. Firing error webhook.")

    # ── Fire the webhook ─────────────────────────────────────────
    # This is how you tell the Orchestrator "I'm done, here are my results"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(webhook_url, json=webhook_payload)
        print(f"[Phase0] Webhook fired. Orchestrator responded: {response.status_code}")
