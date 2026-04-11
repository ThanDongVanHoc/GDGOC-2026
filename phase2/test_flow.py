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

# ── Mock Phase 1 output (simulates what Phase 1 produces) ───────
MOCK_GLOBAL_METADATA = {
    "source_language": "EN",
    "target_language": "VI",
    "license_status": True,
    "author_attribution": "Written by Sarah Johnson",
    "integrity_protection": True,
    "adaptation_rights": False,
    "translation_fidelity": "Strict",
    "plot_alteration": False,
    "cultural_localization": False,
    "preserve_main_names": True,
    "protected_names": ["Luna", "Max", "Professor Whiskers", "Captain Starlight"],
    "no_retouching": True,
    "lock_character_color": True,
    "never_change_rules": [
        "Luna's star-shaped birthmark on her left cheek",
        "Max's red scarf",
    ],
    "style_register": "children_under_10",
    "target_age_tone": 10,
    "glossary_strict_mode": True,
    "sfx_handling": "In_panel_subs",
    "satisfaction_clause": True,
    "allow_bg_edit": True,
    "max_drift_ratio": 0.2,
}

MOCK_STANDARDIZED_PACK = [
    {
        "page_id": 1,
        "width": 595.0,
        "height": 842.0,
        "text_blocks": [
            {
                "content": "The Adventures of Luna and Friends",
                "bbox": [72, 50, 523, 80],
                "font": "Arial-Bold",
                "size": 24.0,
                "color": 0,
                "flags": 1,
                "editability_tag": "editable",
            },
            {
                "content": "Written by Sarah Johnson",
                "bbox": [72, 90, 523, 110],
                "font": "Arial",
                "size": 14.0,
                "color": 0,
                "flags": 0,
                "editability_tag": "non-editable",
            },
        ],
        "image_blocks": [],
    },
    {
        "page_id": 2,
        "width": 595.0,
        "height": 842.0,
        "text_blocks": [
            {
                "content": "Once upon a time, in a land far away, there lived a brave little girl named Luna.",
                "bbox": [72, 100, 523, 130],
                "font": "Georgia",
                "size": 12.0,
                "color": 0,
                "flags": 0,
                "editability_tag": "editable",
            },
            {
                "content": "Luna had a magical star-shaped birthmark on her left cheek that glowed whenever she felt brave.",
                "bbox": [72, 140, 523, 170],
                "font": "Georgia",
                "size": 12.0,
                "color": 0,
                "flags": 0,
                "editability_tag": "editable",
            },
            {
                "content": "Her best friend Max always wore his favorite red scarf, even on the hottest days.",
                "bbox": [72, 180, 523, 210],
                "font": "Georgia",
                "size": 12.0,
                "color": 0,
                "flags": 0,
                "editability_tag": "editable",
            },
        ],
        "image_blocks": [
            {
                "bbox": [50, 250, 545, 600],
                "image_index": 0,
                "editability_tag": "semi-editable",
                "ocr_text_blocks": [
                    {
                        "content": "BOOM!",
                        "bbox_in_image": [100, 20, 200, 60],
                        "confidence": 0.95,
                        "editability_tag": "editable",
                    },
                    {
                        "content": "Let's go, Max!",
                        "bbox_in_image": [250, 100, 400, 140],
                        "confidence": 0.92,
                        "editability_tag": "editable",
                    },
                ],
            }
        ],
    },
    {
        "page_id": 3,
        "width": 595.0,
        "height": 842.0,
        "text_blocks": [
            {
                "content": "\"We must find Professor Whiskers before sunset!\" Luna exclaimed.",
                "bbox": [72, 100, 523, 130],
                "font": "Georgia",
                "size": 12.0,
                "color": 0,
                "flags": 0,
                "editability_tag": "editable",
            },
            {
                "content": "Captain Starlight appeared from behind the clouds, his armor shining like a thousand suns.",
                "bbox": [72, 140, 523, 170],
                "font": "Georgia",
                "size": 12.0,
                "color": 0,
                "flags": 0,
                "editability_tag": "editable",
            },
        ],
        "image_blocks": [],
    },
]

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
    thread_id = str(uuid.uuid4())
    job_payload = {
        "thread_id": thread_id,
        "standardized_pack": MOCK_STANDARDIZED_PACK,
        "global_metadata": MOCK_GLOBAL_METADATA,
        "webhook_url": WEBHOOK_URL,
    }

    print(f"\n[Test] Sending job to Phase 2...")
    print(f"  thread_id: {thread_id}")
    print(f"  Pages: {len(MOCK_STANDARDIZED_PACK)}")
    print(f"  Protected names: {MOCK_GLOBAL_METADATA['protected_names']}")
    print(f"  webhook_url: {WEBHOOK_URL}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PHASE2_URL}/api/v1/phase2/run", json=job_payload
        )
        print(f"\n[Test] Phase 2 responded: {response.status_code} {response.json()}")

    # ── Step 3: Wait for webhook ─────────────────────────────────
    print("\n[Test] Waiting for webhook callback (this may take 30-90s)...")
    result_event.wait(timeout=180)

    if not received_result:
        print("\n[Test] ❌ TIMEOUT — no webhook received in 180 seconds!")
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
            icon = "📝" if src == "text" else "✏️"
            orig = block["original_content"][:50]
            trans = block["translated_content"][:50]
            warn = " ⚠️" if block.get("warning") else ""
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
            print("\n  ✅ No warnings — all translations passed review!")

    print("\n" + "=" * 70)
    print("  Phase 2 test complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
