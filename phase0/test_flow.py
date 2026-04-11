"""
Phase 0 — End-to-End Test Script.

=== RUN THIS TO SEE THE FULL FLOW ===

This script simulates the Orchestrator:
    1. Starts a tiny webhook server to receive results
    2. Sends a job to the Phase 0 service
    3. Waits for the webhook callback
    4. Prints the results

Usage:
    # Terminal 1: Start Phase 0 service
    uvicorn app.main:app --reload --port 8010

    # Terminal 2: Run this test
    python test_flow.py
"""

import asyncio
import json
import threading
import time
import uuid

import httpx
import uvicorn
from fastapi import FastAPI

# ── Configuration ────────────────────────────────────────────────
PHASE0_URL = "http://localhost:8010"
WEBHOOK_PORT = 9999
WEBHOOK_URL = f"http://localhost:{WEBHOOK_PORT}/webhook"

# ── Webhook receiver (simulates Orchestrator) ────────────────────
webhook_app = FastAPI()
received_result = {}
result_event = threading.Event()


@webhook_app.post("/webhook")
async def receive_webhook(payload: dict) -> dict:
    """This is what the Orchestrator's webhook endpoint looks like."""
    global received_result
    received_result = payload
    result_event.set()
    return {"status": "received"}


def start_webhook_server():
    """Start webhook server in a background thread."""
    uvicorn.run(webhook_app, host="0.0.0.0", port=WEBHOOK_PORT, log_level="warning")


async def main():
    print("=" * 60)
    print("  OmniLocal Phase 0 — End-to-End Test")
    print("=" * 60)

    # ── Step 1: Start webhook server ─────────────────────────────
    print("\n[Test] Starting webhook receiver on port", WEBHOOK_PORT)
    webhook_thread = threading.Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    time.sleep(1)  # Wait for server to start

    # ── Step 2: Send job to Phase 0 ──────────────────────────────
    thread_id = str(uuid.uuid4())
    job_payload = {
        "thread_id": thread_id,
        "image_path": "data/input/sample.png",  # Will auto-generate if not found
        "webhook_url": WEBHOOK_URL,
    }

    print(f"\n[Test] Sending job to Phase 0...")
    print(f"  thread_id: {thread_id}")
    print(f"  image_path: {job_payload['image_path']}")
    print(f"  webhook_url: {WEBHOOK_URL}")

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{PHASE0_URL}/api/v1/phase0/run", json=job_payload)
        print(f"\n[Test] Phase 0 responded: {response.status_code} {response.json()}")

    # ── Step 3: Wait for webhook ─────────────────────────────────
    print("\n[Test] Waiting for webhook callback...")
    result_event.wait(timeout=30)

    if not received_result:
        print("\n[Test] TIMEOUT -- no webhook received in 30 seconds!")
        return

    # -- Step 4: Print results ----------------------------------------
    print("\n[Test] OK -- Webhook received!")
    print(f"  thread_id: {received_result.get('thread_id')}")

    if received_result.get("error"):
        print(f"  ERROR: {received_result['error']}")
    else:
        result = received_result.get("result", {})
        print(f"  Image size: {result.get('image_width')}x{result.get('image_height')}")
        print(f"  Contours found: {result.get('contour_count')}")
        print(f"  Significant regions: {len(result.get('significant_regions', []))}")
        print(f"  Output saved to: {result.get('output_path')}")

    print("\n" + "=" * 60)
    print("  Flow complete! This is exactly how the Orchestrator works:")
    print("  1. Sent job via POST -> got 202 Accepted")
    print("  2. Worker processed in background")
    print("  3. Worker fired webhook with results")
    print("  4. Orchestrator (this script) received results")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
