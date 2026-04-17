import json
import logging
import os
import subprocess
import sys
import time
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_PDF_PATH = os.path.join(PROJECT_ROOT, "..", "test.pdf")

PHASE1_PORT = 8001
PHASE2_PORT = 8002

def wait_for_server(url, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = httpx.get(url)
            if r.status_code in (200, 404, 405):  # Any response means it's up
                return True
        except httpx.ConnectError:
            time.sleep(0.5)
    return False

def test_phase1():
    base_url = f"http://localhost:{PHASE1_PORT}/api/v1"
    logger.info("Testing Phase 1 at %s", base_url)
    
    # 1. Global Metadata GET (before any extraction might be None or default)
    r = httpx.get(f"{base_url}/global-metadata")
    logger.info("GET /global-metadata -> %d", r.status_code)
    
    # 2. Upload PDF
    logger.info("Uploading PDF: %s", TEST_PDF_PATH)
    with open(TEST_PDF_PATH, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        r = httpx.post(f"{base_url}/upload", files=files, timeout=60.0)
        logger.info("POST /upload -> %d", r.status_code)
        if r.status_code != 200:
            logger.error("Upload failed: %s", r.text)
            return False
            
    # 3. GET Task Graph
    r = httpx.get(f"{base_url}/task-graph")
    logger.info("GET /task-graph -> %d", r.status_code)
    if r.status_code != 200:
        logger.error("Failed to get task graph: %s", r.text)
        return False
        
    pack = r.json()
    logger.info("Task graph retrieved successfully. Pages: %d", len(pack.get("pages", [])))
    return True

def test_phase2():
    base_url = f"http://localhost:{PHASE2_PORT}/api/v1"
    phase1_url = f"http://localhost:{PHASE1_PORT}"
    logger.info("Testing Phase 2 at %s", base_url)
    
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        logger.warning("GEMINI_API_KEY is not set. The translation will fail, but we'll try to reach the endpoint.")
        
    payload = {
        "phase1_base_url": phase1_url,
        "gemini_api_key": gemini_key
    }
    
    # POST /translate
    logger.info("Triggering POST /translate")
    r = httpx.post(f"{base_url}/translate", json=payload, timeout=300.0)
    logger.info("POST /translate -> %d", r.status_code)
    
    if r.status_code == 200:
        verified_packs = r.json()
        logger.info("Translation successful. Extracted %d packs", len(verified_packs))
    else:
        logger.error("Translation returned %d: %s", r.status_code, r.text)
        if not gemini_key and r.status_code == 400:
            logger.info("Expected 400 because GEMINI_API_KEY is missing.")
            return True
        return False
        
    # GET /verified-text/warnings
    r = httpx.get(f"{base_url}/verified-text/warnings")
    logger.info("GET /verified-text/warnings -> %d", r.status_code)
    
    return True

def main():
    logger.info("Starting FastAPI services...")
    p1 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "phase1.main:app", "--port", str(PHASE1_PORT)],
        cwd=PROJECT_ROOT
    )
    p2 = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "phase2.main:app", "--port", str(PHASE2_PORT)],
        cwd=PROJECT_ROOT
    )
    
    try:
        # Wait for both servers to be listening
        p1_ready = wait_for_server(f"http://localhost:{PHASE1_PORT}/docs")
        p2_ready = wait_for_server(f"http://localhost:{PHASE2_PORT}/docs")
        
        if not p1_ready or not p2_ready:
            logger.error("Servers did not start properly.")
            sys.exit(1)
            
        logger.info("Servers are up. Proceeding with E2E tests.")
        
        success1 = test_phase1()
        success2 = test_phase2()
        
        if success1 and success2:
            logger.info("========== ALL TESTS PASSED ==========")
        else:
            logger.error("========== SOME TESTS FAILED ==========")
            
    finally:
        logger.info("Shutting down servers...")
        p1.terminate()
        p2.terminate()
        p1.wait()
        p2.wait()

if __name__ == "__main__":
    main()
