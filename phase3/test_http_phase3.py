import asyncio
import json
import logging
import os
import sys
import time

import httpx

# Paths to dummy data
_DATA_DIR = os.path.join(os.path.dirname(__file__), "dummy_data")
_PHASE1_PATH = os.path.join(_DATA_DIR, "phase1_result.json")
_PHASE2_PATH = os.path.join(_DATA_DIR, "phase2_result.json")

def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _build_payload() -> dict:
    """Build the Orchestrator payload that Phase 3 would receive."""
    phase1 = _load_json(_PHASE1_PATH)
    phase2 = _load_json(_PHASE2_PATH)

    phase1_result = phase1.get("result", phase1)
    phase2_result = phase2.get("result", phase2)

    return {
        "thread_id": "test-http-phase3",
        "webhook_url": "http://localhost:8003/webhook/test", # Phase 3's built-in mock webhook target
        "global_metadata": phase1_result.get("global_metadata", {}),
        "output_phase_1": phase1_result.get("standardized_pack", []),
        "output_phase_2": {
            "verified_text_pack": phase2_result.get("verified_text_pack", []),
            "translation_warnings": phase2_result.get("translation_warnings", []),
        },
        "source_pdf_path": os.path.join(os.path.dirname(__file__), "data", "uploads", "source.pdf"),
        "use_llm": True,
    }

async def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    
    payload = _build_payload()
    phase3_url = "http://localhost:8003/api/v1/phase3/run"
    test_webhook_url = "http://localhost:8003/webhook/test/test-http-phase3"

    print(f"Sending async job to Phase 3 at {phase3_url}...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(phase3_url, json=payload)
            response.raise_for_status()
            print(f"Phase 3 Accepted Job: {response.json()}")
        except Exception as e:
            print(f"Failed to submit job to Phase 3: {e}")
            return
            
        print("Polling webhook for completion...")
        for _ in range(30):
            await asyncio.sleep(2)
            try:
                res = await client.get(test_webhook_url)
                data = res.json()
                if data:
                    print("\n========== WEBHOOK RESULT RECEIVED ==========")
                    output_path = os.path.join(_DATA_DIR, "phase3_http_result.json")
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"Success! Output saved to: {output_path}")
                    
                    # Print short summary
                    out_p3 = data.get("output_phase_3", {})
                    log = out_p3.get("localization_log", [])
                    print(f"Proposals processed: {len(log)}")
                    print(f"Errors?: {data.get('error')}")
                    return
            except Exception:
                pass
            print(".", end="", flush=True)
            
        print("\nTimeout waiting for Phase 3 webhook callback.")

if __name__ == "__main__":
    asyncio.run(main())
