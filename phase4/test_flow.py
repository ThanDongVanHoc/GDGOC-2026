"""
Phase 4 — End-to-End Test Script.

Simulates the Orchestrator sending a job to Phase 4:
    1. Starts a webhook server to receive results.
    2. Sends a job with an image path and a JSON replacements payload.
    3. Waits for the webhook callback.
    4. Prints the localized image output path.

Usage:
    # Terminal 1: Start Phase 4 service
    cd phase4
    uvicorn app.main:app --reload --port 8000

    # Terminal 2: Run this test
    cd phase4
    python test_flow.py
"""

import asyncio
import json
import os
import threading
import time
import uuid

import httpx
import uvicorn
from fastapi import FastAPI

# ── Configuration ────────────────────────────────────────────────
PHASE4_URL = "http://localhost:8004"
WEBHOOK_PORT = 9994
WEBHOOK_URL = f"http://localhost:{WEBHOOK_PORT}/webhook"

# Path to test image — adjust if needed
TEST_IMAGE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "uploads", "sample_image.png")
)

# Sample JSON payload
SAMPLE_REPLACEMENTS = {
    "Background": {
        "scene_type": "indoor",
        "preserved_foreground": [],
        "modified_background_elements": [],
        "vietnamese_setting_suggestions": [],
        "constraints": []
    },
    "Object_Replacement": {}
}

# ── Webhook receiver (simulates Orchestrator) ────────────────────
webhook_app = FastAPI()
received_result = {}
result_event = threading.Event()


@webhook_app.post("/webhook")
async def receive_webhook(payload: dict) -> dict:
    """Receive Phase 4 processing results via webhook callback."""
    global received_result
    received_result = payload
    result_event.set()
    return {"status": "received"}


def start_webhook_server():
    """Start webhook server in a background thread."""
    uvicorn.run(webhook_app, host="0.0.0.0", port=WEBHOOK_PORT, log_level="warning")


async def main():
    print("=" * 70)
    print("  OmniLocal Phase 4 — End-to-End Test")
    print("=" * 70)

    # ── Step 1: Start webhook server ─────────────────────────────
    print(f"\n[Test] Starting webhook receiver on port {WEBHOOK_PORT}")
    webhook_thread = threading.Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    time.sleep(1)

    # ── Step 2: Send job to Phase 4 ──────────────────────────────
    thread_id = str(uuid.uuid4())
    job_payload = {
        "thread_id": thread_id,
        "webhook_url": WEBHOOK_URL,
        "tasks": [
            {
                "image_url": "https://images.dog.ceo/breeds/pomeranian/n02112018_1090.jpg", # Real dog image URL for testing
                "replacements_json": SAMPLE_REPLACEMENTS
            }
        ]
    }

    print(f"\n[Test] Sending job to Phase 4...")
    print(f"  thread_id: {thread_id}")
    print(f"  tasks: 1 image URL queued")
    print(f"  webhook_url: {WEBHOOK_URL}")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PHASE4_URL}/api/v1/phase4/run", json=job_payload
            )
            print(f"\n[Test] Phase 4 responded: {response.status_code} {response.json()}")
        except httpx.ConnectError:
            print(f"\n[Test] ❌ ERROR: Could not connect to Phase 4 service at {PHASE4_URL}")
            print("Make sure Phase 4 is running via: uvicorn app.main:app --port 8000")
            return

    # ── Step 3: Wait for webhook ─────────────────────────────────
    print("\n[Test] Waiting for webhook callback (this may take 1-5 minutes)...")
    result_event.wait(timeout=600)

    if not received_result:
        print("\n[Test] ❌ TIMEOUT — no webhook received in 600 seconds!")
        return

    # ── Step 4: Print results ────────────────────────────────────
    print("\n[Test] ✅ Webhook received!")
    print(f"  thread_id: {received_result.get('thread_id')}")

    if received_result.get("error"):
        print(f"  ❌ ERROR: {received_result['error']}")
    else:
        result = received_result.get("result", {})
        tasks_results = result.get("results", [])
        
        print("\n  --- Phase 4 Results ---")
        print(f"  Overall Status: {result.get('status', 'N/A')}")
        for i, tr in enumerate(tasks_results):
            print(f"  [Task {i+1}] Status: {tr.get('status')}")
            if 'image' in tr and tr['image']:
                b64_preview = tr['image'][:50] + "..."
                print(f"           Image (B64): {b64_preview}")
            elif 'message' in tr:
                print(f"           Error:       {tr.get('message')}")
        
        with open("phase4_result.json", "w", encoding="utf-8") as f:
            json.dump(received_result, f, ensure_ascii=False, indent=2)
        print(f"\n[Test] Results successfully saved to phase4_result.json")

    print("\n" + "=" * 70)
    print("  Phase 4 test complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
