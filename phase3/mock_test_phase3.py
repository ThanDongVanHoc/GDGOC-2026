import asyncio
import json
import os
import sys
import time
import httpx

# Paths to dummy data
_DATA_DIR = os.path.join(os.path.dirname(__file__), "dummy_data")
_PAYLOAD_PATH = os.path.join(_DATA_DIR, "phase3_payload.json")

async def run_mock_test():
    if not os.path.exists(_PAYLOAD_PATH):
        print(f"Error: {_PAYLOAD_PATH} not found.")
        return

    print(f"Loading payload from {_PAYLOAD_PATH}...")
    with open(_PAYLOAD_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Override webhook_url to use the Phase 3 built-in test webhook
    thread_id = payload.get("thread_id", "mock-test-id")
    payload["webhook_url"] = "http://localhost:8003/webhook/test"
    # Ensure source_pdf_path is absolute or relative to where uvicorn runs
    # In this mock, we'll just use the one in the payload or fall back
    if not payload.get("source_pdf_path"):
        payload["source_pdf_path"] = os.path.join(os.path.dirname(__file__), "data", "uploads", "source.pdf")

    phase3_url = "http://localhost:8003/api/v1/phase3/run"
    test_webhook_url = f"http://localhost:8003/webhook/test/{thread_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"Firing payload into Phase 3 at {phase3_url}...")
        try:
            response = await client.post(phase3_url, json=payload)
            if response.status_code == 202:
                print(f"Accepted: {response.json()}")
            else:
                print(f"Failed to submit: {response.status_code} - {response.text}")
                return
        except Exception as e:
            print(f"Error connecting to Phase 3: {e}")
            print("Make sure the Phase 3 service is running on port 8003.")
            return

        print(f"Polling test webhook for thread '{thread_id}'...")
        start_time = time.time()
        timeout = 60  # 1 minute timeout
        
        while time.time() - start_time < timeout:
            try:
                res = await client.get(test_webhook_url)
                if res.status_code == 200:
                    data = res.json()
                    if data:
                        print("\n" + "="*50)
                        print("SUCCESS: Webhook Result Received!")
                        print("="*50)
                        
                        output_file = os.path.join(_DATA_DIR, "mock_test_result.json")
                        with open(output_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        
                        print(f"Result saved to: {output_file}")
                        
                        out_p3 = data.get("output_phase_3", {})
                        log = out_p3.get("localization_log", [])
                        safe_pack = out_p3.get("context_safe_localized_text_pack", [])
                        
                        print(f"Proposals processed: {len(log)}")
                        print(f"Safe text blocks: {len(safe_pack)}")
                        if data.get("error"):
                            print(f"Error in processing: {data.get('error')}")
                        return
                    else:
                        print(".", end="", flush=True)
                else:
                    print(f"Webhook poll status: {res.status_code}")
            except Exception as e:
                print(f"Polling error: {e}")
            
            await asyncio.sleep(2)
        
        print("\nTimeout: Result not received in 60 seconds.")

if __name__ == "__main__":
    asyncio.run(run_mock_test())
