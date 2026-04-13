"""
Phase 1 — End-to-End Test Script.

Simulates the Orchestrator sending a job to Phase 1:
    1. Starts a webhook server to receive results.
    2. Sends a job with a PDF and a sample brief.
    3. Waits for the webhook callback.
    4. Prints the standardized pack output.

Usage:
    # Terminal 1: Start Phase 1 service
    cd phase1
    uvicorn app.main:app --reload --port 8001

    # Terminal 2: Run this test
    cd phase1
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
PHASE1_URL = "http://localhost:8001"
WEBHOOK_PORT = 9991
WEBHOOK_URL = f"http://localhost:{WEBHOOK_PORT}/webhook"

# Path to test PDF — adjust if needed
TEST_PDF_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "uploads", "test.pdf")
)

# Sample project brief text (simulates client email)
SAMPLE_BRIEF_TEXT = """
Project Brief — Children's Book Localization

Book Title: "Cinderella: The Enchanted Ball"
Source Language: English (EN)
Target Language: Vietnamese (VI)

Translation Style: Use simple, warm language suitable for children under 10 years old.

Copyright Constraints:
- The book is legally licensed for Vietnamese translation.
- Author credit: "Written by Charles Perrault"
- Do NOT change the plot or storyline in any way.
- Cultural localization is NOT allowed — keep all cultural references as-is.

Character & Brand Rules:
- Keep the following character names untranslated: Cinderella, Prince Charming, Fairy Godmother, Lady Tremaine
- Do NOT retouch or redraw any character illustrations.
- Character colors MUST remain exactly as in the original (locked).
- Never change: Cinderella's glass slippers, the Fairy Godmother's sparkling wand.

Editorial Guidelines:
- Glossary strict mode is ON — use provided terminology consistently.
- SFX (sound effects like BONG, SWISH): Add small Vietnamese subtitle next to the original.
- The original publisher has the right to review and veto the final translation.

Technical Notes:
- Allow background editing for text placement adjustments.
- Maximum text length drift: 20% compared to source text.
"""

# ── Webhook receiver (simulates Orchestrator) ────────────────────
webhook_app = FastAPI()
received_result = {}
result_event = threading.Event()


@webhook_app.post("/webhook")
async def receive_webhook(payload: dict) -> dict:
    """Receive Phase 1 processing results via webhook callback."""
    global received_result
    received_result = payload
    result_event.set()
    return {"status": "received"}


def start_webhook_server():
    """Start webhook server in a background thread."""
    uvicorn.run(webhook_app, host="0.0.0.0", port=WEBHOOK_PORT, log_level="warning")


async def main():
    print("=" * 70)
    print("  OmniLocal Phase 1 — End-to-End Test")
    print("=" * 70)

    # ── Step 1: Start webhook server ─────────────────────────────
    print(f"\n[Test] Starting webhook receiver on port {WEBHOOK_PORT}")
    webhook_thread = threading.Thread(target=start_webhook_server, daemon=True)
    webhook_thread.start()
    time.sleep(1)

    # ── Step 2: Send job to Phase 1 ──────────────────────────────
    thread_id = str(uuid.uuid4())
    job_payload = {
        "thread_id": thread_id,
        "source_pdf_path": TEST_PDF_PATH,
        "brief_text": SAMPLE_BRIEF_TEXT,
        "brief_path": "",
        "webhook_url": WEBHOOK_URL,
    }

    print(f"\n[Test] Sending job to Phase 1...")
    print(f"  thread_id: {thread_id}")
    print(f"  source_pdf_path: {TEST_PDF_PATH}")
    print(f"  webhook_url: {WEBHOOK_URL}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PHASE1_URL}/api/v1/phase1/run", json=job_payload
        )
        print(f"\n[Test] Phase 1 responded: {response.status_code} {response.json()}")

    # ── Step 3: Wait for webhook ─────────────────────────────────
    print("\n[Test] Waiting for webhook callback (this may take 30-60s)...")
    result_event.wait(timeout=120)

    if not received_result:
        print("\n[Test] ❌ TIMEOUT — no webhook received in 120 seconds!")
        return

    # ── Step 4: Print results ────────────────────────────────────
    print("\n[Test] ✅ Webhook received!")
    print(f"  thread_id: {received_result.get('thread_id')}")

    if received_result.get("error"):
        print(f"  ❌ ERROR: {received_result['error']}")
    else:
        result = received_result.get("result", {})

        # Global Metadata
        metadata = result.get("global_metadata", {})
        print("\n  --- Global Metadata ---")
        print(f"  Source: {metadata.get('source_language')} → {metadata.get('target_language')}")
        print(f"  Style: {metadata.get('style_register')}")
        print(f"  Protected names: {metadata.get('protected_names')}")
        print(f"  Lock character color: {metadata.get('lock_character_color')}")

        # Standardized Pack
        pack = result.get("standardized_pack", [])
        print(f"\n  --- Standardized Pack ({len(pack)} pages) ---")
        for page in pack[:3]:  # Show first 3 pages
            print(f"\n  Page {page['page_id']} ({page['width']:.0f}x{page['height']:.0f})")
            print(f"    Text blocks: {len(page.get('text_blocks', []))}")
            print(f"    Image blocks: {len(page.get('image_blocks', []))}")

            for tb in page.get("text_blocks", [])[:2]:
                text_preview = tb["content"][:60] + "..." if len(tb["content"]) > 60 else tb["content"]
                print(f"    📝 [{tb['editability_tag']}] \"{text_preview}\"")

            for ib in page.get("image_blocks", []):
                ocr_count = len(ib.get("ocr_text_blocks", []))
                print(f"    🖼️ [{ib['editability_tag']}] Image (OCR: {ocr_count} texts)")
                for ocr in ib.get("ocr_text_blocks", [])[:2]:
                    print(f"      ✏️ [{ocr['editability_tag']}] \"{ocr['content']}\" (conf={ocr['confidence']:.2f})")

        if len(pack) > 3:
            print(f"\n  ... and {len(pack) - 3} more pages")

        with open("phase1_result.json", "w", encoding="utf-8") as f:
            json.dump(received_result, f, ensure_ascii=False, indent=2)
        print(f"\n[Test] Results successfully saved to phase1_result.json")

    print("\n" + "=" * 70)
    print("  Phase 1 test complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
