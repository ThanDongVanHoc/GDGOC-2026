"""
OmniLocal — Phase 3 Service: Cultural Localization & Butterfly Effect.
"""

import httpx
from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import HTMLResponse

from app.worker import run as run_worker

app = FastAPI(title="OmniLocal Phase 3 — Localization & Butterfly Effect")


@app.get("/")
async def health() -> dict:
    return {"service": "Phase 3 — Localization", "status": "running"}


_TEST_WEBHOOK_RESULTS = {}


@app.post("/webhook/test")
async def test_webhook(payload: dict) -> dict:
    _TEST_WEBHOOK_RESULTS[payload.get("thread_id")] = payload
    return {"status": "received"}


@app.get("/webhook/test/{thread_id}")
async def get_test_webhook(thread_id: str) -> dict:
    return _TEST_WEBHOOK_RESULTS.get(thread_id, {})


@app.get("/test", response_class=HTMLResponse)
async def test_ui() -> str:
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Phase 3 Test UI</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 40px auto; }
        textarea { width: 100%; height: 300px; font-family: monospace; margin-bottom: 10px; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; min-height: 50px; }
        button { padding: 10px 15px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; }
        button:hover { background: #0056b3; }
        .row { display: flex; gap: 20px; }
        .col { flex: 1; min-width: 0; }
    </style>
</head>
<body>
    <h1>Phase 3 Test UI</h1>
    <p>Submit JSON payload to Phase 3. The test webhook endpoint is automatically configured to receive results.</p>
    
    <div class="row">
        <div class="col">
            <h3>Request Payload</h3>
            <textarea id="payloadInput">{
  "thread_id": "test-123",
  "webhook_url": "http://localhost:8003/webhook/test",
  "global_metadata": {
    "cultural_context": "Vietnam",
    "target_language": "vi",
    "protected_names": ["Harry"]
  },
  "output_phase_2": {
    "verified_text_pack": [
      {
        "original_content": "Harry sat by the Fireplace in a Wool Hat.",
        "translated_content": "Harry ngồi bên lò sưởi trong chiếc mũ len.",
        "bbox": [0, 0, 100, 20],
        "page_id": 1,
        "source_type": "text"
      }
    ],
    "translation_warnings": []
  }
}</textarea>
            <br>
            <button onclick="submitJob()">Run Phase 3</button>
        </div>
        <div class="col">
            <h3>Async Status & Output</h3>
            <pre id="outputView">Waiting for submission...</pre>
        </div>
    </div>

    <script>
        let pollInterval;
        async function submitJob() {
            const btn = document.querySelector('button');
            const out = document.getElementById('outputView');
            btn.disabled = true;
            out.textContent = "Submitting...";
            clearInterval(pollInterval);
            
            try {
                const payload = JSON.parse(document.getElementById('payloadInput').value);
                const threadId = payload.thread_id;
                
                if (!payload.webhook_url.includes('/webhook/test')) {
                    payload.webhook_url = window.location.origin + "/webhook/test";
                }
                
                const res = await fetch("/api/v1/phase3/run", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                
                const data = await res.json();
                out.textContent = `Accepted:\\n${JSON.stringify(data, null, 2)}\\n\\nPolling test webhook for thread '${threadId}'...`;
                
                pollInterval = setInterval(async () => {
                    const statusRes = await fetch(`/webhook/test/${threadId}`);
                    const statusData = await statusRes.json();
                    if (Object.keys(statusData).length > 0) {
                        clearInterval(pollInterval);
                        out.textContent = `Webhook Received!\\n\\n` + JSON.stringify(statusData, null, 2);
                        btn.disabled = false;
                    } else {
                        out.textContent += ".";
                    }
                }, 2000);
            } catch (err) {
                out.textContent = "Error: " + err.message;
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
"""


@app.post("/api/v1/phase3/run", status_code=202)
async def run_phase(payload: dict, background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(_process_and_callback, payload)
    return {"status": "accepted", "thread_id": payload["thread_id"]}


async def _process_and_callback(payload: dict) -> None:
    thread_id = payload["thread_id"]
    webhook_url = payload["webhook_url"]
    try:
        result = await run_worker(payload)
        webhook_body = {
            "thread_id": thread_id,
            "output_phase_3": result.get("output_phase_3", {}),
            "localization_warnings": result.get("localization_warnings", []),
            "error": None,
        }
    except Exception as e:
        webhook_body = {
            "thread_id": thread_id,
            "output_phase_3": {},
            "localization_warnings": [],
            "error": str(e),
        }
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(webhook_url, json=webhook_body)
