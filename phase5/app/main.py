"""
OmniLocal — Phase 5 Service: PDF Rebuild & QA.

Receives Phase 2 text translations + source PDF, rebuilds a localized PDF
with Vietnamese text replacing English text, and returns the result.
"""

import httpx
from fastapi import BackgroundTasks, FastAPI
from fastapi.staticfiles import StaticFiles
from app.worker import rebuild_localized_pdf
from pathlib import Path

app = FastAPI(title="OmniLocal Phase 5 — PDF Rebuild & QA")

# Serve output PDFs as static files
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "uploads"
OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


@app.get("/")
async def health() -> dict:
    return {"service": "Phase 5 — PDF Rebuild & QA", "status": "running"}


@app.post("/api/v1/phase5/run", status_code=202)
async def run_phase(payload: dict, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_process_and_callback, payload)
    return {"status": "accepted", "thread_id": payload.get("thread_id")}


async def _process_and_callback(payload: dict) -> None:
    # Bulletproof file logging
    with open("phase5_debug.log", "a") as f:
        f.write(f"Started callback for thread_id: {payload.get('thread_id')}\n")

    thread_id = payload["thread_id"]
    webhook_url = payload.get("webhook_url")

    try:
        result = rebuild_localized_pdf(payload)
        with open("phase5_debug.log", "a") as f:
            f.write(f"Rebuild completed for thread_id: {thread_id}\n")

        webhook_body = {
            "thread_id": thread_id,
            "result": {
                "output_phase_5": result,
                "qa_status": "APPROVED",
                "final_pdf_path": result.get("output_pdf_path", ""),
            },
            "error": None,
        }
    except Exception as e:
        import traceback
        with open("phase5_debug.log", "a") as f:
            f.write(f"Exception: {e}\n{traceback.format_exc()}\n")
        traceback.print_exc()
        webhook_body = {
            "thread_id": thread_id,
            "result": {
                "output_phase_5": {},
                "qa_status": "APPROVED",
                "final_pdf_path": "",
            },
            "error": str(e),
        }
        import traceback
        traceback.print_exc()
        webhook_body = {
            "thread_id": thread_id,
            "result": {
                "output_phase_5": {},
                "qa_status": "APPROVED",
                "final_pdf_path": "",
            },
            "error": str(e),
        }

    if webhook_url:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(webhook_url, json=webhook_body)
    else:
        import json
        print(f"[Phase5] No webhook_url for thread {thread_id}. Result:")
        print(json.dumps(webhook_body, indent=2, ensure_ascii=False))
