"""
Phase 2 — End-to-End Test Script.

Simulates the Orchestrator sending Phase 1 output to Phase 2:
    1. Starts a webhook server to receive results.
    2. Sends a job with mock standardized_pack and global_metadata.
    3. Waits for the webhook callback.
    4. Prints the verified text pack output.

Usage:
    # Terminal 1: Start Phase 2 service
    cd phase2
    uvicorn app.main:app --reload --port 8002

    # Terminal 2: Run this test
    cd phase2
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
PHASE2_URL = "http://localhost:8002"
WEBHOOK_PORT = 9992
WEBHOOK_URL = f"http://localhost:{WEBHOOK_PORT}/webhook"

# ── Input from Phase 1 ──────────────────────────────────────────
PHASE1_RESULT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "phase1", "phase1_result.json")
)

def load_phase1_output():
    if not os.path.exists(PHASE1_RESULT_PATH):
        raise FileNotFoundError(f"Missing Phase 1 output at {PHASE1_RESULT_PATH}. Run Phase 1 test first.")
    with open(PHASE1_RESULT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    result = data.get("result", {})
    return result.get("standardized_pack", []), result.get("global_metadata", {})

# ── Webhook receiver (simulates Orchestrator) ────────────────────
webhook_app = FastAPI()
received_result = {}
result_event = threading.Event()


@webhook_app.post("/webhook")
async def receive_webhook(payload: dict) -> dict:
    """Receive Phase 2 processing results via webhook callback."""
    global received_result
    received_result = payload
    result_event.set()
    return {"status": "received"}


def start_webhook_server():
    """Start webhook server in a background thread."""
    uvicorn.run(webhook_app, host="0.0.0.0", port=WEBHOOK_PORT, log_level="warning")


async def main():
    print("=" * 70)
    print("  OmniLocal Phase 2 — End-to-End Test")
    print("=" * 70)

    # ── Step 1: Start webhook server ─────────────────────────────
    print(f"\n[Test] Starting webhook receiver on port {WEBHOOK_PORT}")
    webhook_thread = threading.Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    time.sleep(1)

    # ── Step 2: Send job to Phase 2 ──────────────────────────────
    try:
        pack, metadata = load_phase1_output()
    except Exception as e:
        print(f"\n[Test] ERROR loading Phase 1 output: {e}")
        return

    thread_id = str(uuid.uuid4())
    job_payload = {
        "thread_id": thread_id,
        "standardized_pack": pack,
        "global_metadata": metadata,
        "webhook_url": WEBHOOK_URL,
    }

    print(f"\n[Test] Sending job to Phase 2...")
    print(f"  thread_id: {thread_id}")
    print(f"  Pages: {len(pack)}")
    print(f"  Protected names: {metadata.get('protected_names', [])}")
    print(f"  webhook_url: {WEBHOOK_URL}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{PHASE2_URL}/api/v1/phase2/run", json=job_payload
        )
        print(f"\n[Test] Phase 2 responded: {response.status_code} {response.json()}")

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

        # Verified Text Pack
        pack = result.get("verified_text_pack", [])
        warnings = result.get("translation_warnings", [])
        print(f"\n  --- Verified Text Pack ({len(pack)} blocks) ---")

        for block in pack:
            src = block.get("source_type", "text")
            icon = "- " if src == "text" else "* "
            orig = block["original_content"][:50]
            trans = block["translated_content"][:50]
            warn = " [WARN]" if block.get("warning") else ""
            print(f"  {icon} [p{block['page_id']}] \"{orig}\"")
            print(f"     → \"{trans}\"{warn}")

        # Warnings
        if warnings:
            print(f"\n  --- Translation Warnings ({len(warnings)}) ---")
            for w in warnings:
                print(
                    f"  ⚠️ Chunk {w['chunk_id']} (pages {w['page_range']}): "
                    f"Score {w['final_score']}/10 — {w['reason']}"
                )
        else:
            print("\n  [OK] No warnings — all translations passed review!")

        with open("phase2_result.json", "w", encoding="utf-8") as f:
            json.dump(received_result, f, ensure_ascii=False, indent=2)
        print(f"\n[Test] Results successfully saved to phase2_result.json")

    print("\n" + "=" * 70)
    print("  Phase 2 test complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
