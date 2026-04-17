import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
import uvicorn
import logging

import worker

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Phase 1 Worker API", description="Standalone FastAPI wrapper for Phase 1 Worker")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase1_app")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "phase1-worker"}


@app.post("/api/v1/process")
async def process_phase1(
    source_pdf: UploadFile = File(..., description="PDF file to process"),
    brief_file: UploadFile = File(None, description="Optional brief file (.txt/.docx)"),
    brief_text: str = Form("", description="Optional raw brief text"),
    thread_id: str = Form("default_thread"),
):
    # ── Save uploaded PDF to disk ────────────────────────────────
    file_id = uuid.uuid4().hex[:12]
    pdf_path = UPLOAD_DIR / f"{file_id}_{source_pdf.filename}"

    try:
        with open(pdf_path, "wb") as f:
            shutil.copyfileobj(source_pdf.file, f)
        logger.info(f"Saved uploaded PDF → {pdf_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save PDF: {e}")

    # ── Save optional brief file ─────────────────────────────────
    brief_path = ""
    if brief_file and brief_file.filename:
        brief_path = str(UPLOAD_DIR / f"{file_id}_{brief_file.filename}")
        with open(brief_path, "wb") as f:
            shutil.copyfileobj(brief_file.file, f)
        logger.info(f"Saved uploaded brief → {brief_path}")

    # ── Build payload and run worker ─────────────────────────────
    payload = {
        "source_pdf_path": str(pdf_path),
        "brief_path": brief_path,
        "brief_text": brief_text,
        "thread_id": thread_id,
    }

    try:
        logger.info(f"Processing Phase 1 for thread_id={thread_id}")
        result = await worker.run(payload)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.exception("Error processing Phase 1 payload")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up uploaded files after processing
        pdf_path.unlink(missing_ok=True)
        if brief_path:
            Path(brief_path).unlink(missing_ok=True)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=1234, reload=True)