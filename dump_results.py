import asyncio
import json
import os
import sys

sys.path.append(os.path.abspath('phase1'))
sys.path.append(os.path.abspath('phase2'))

from phase1.app.worker import run as run_phase1
from phase2.app.worker import run as run_phase2
from phase1.test_flow import SAMPLE_BRIEF_TEXT, TEST_PDF_PATH
from phase2.test_flow import MOCK_GLOBAL_METADATA, MOCK_STANDARDIZED_PACK

async def main():
    print("Running Phase 1...")
    p1_payload = {
        "thread_id": "test_phase1",
        "source_pdf_path": TEST_PDF_PATH,
        "brief_text": SAMPLE_BRIEF_TEXT,
        "brief_path": "",
    }
    p1_result = await run_phase1(p1_payload)
    with open("phase1_result.json", "w", encoding="utf-8") as f:
        json.dump(p1_result, f, indent=2, ensure_ascii=False)
    print("Phase 1 done. Saved to phase1_result.json")

    print("Running Phase 2...")
    p2_payload = {
        "thread_id": "test_phase2",
        "standardized_pack": MOCK_STANDARDIZED_PACK,
        "global_metadata": MOCK_GLOBAL_METADATA,
    }
    p2_result = await run_phase2(p2_payload)
    with open("phase2_result.json", "w", encoding="utf-8") as f:
        json.dump(p2_result, f, indent=2, ensure_ascii=False)
    print("Phase 2 done. Saved to phase2_result.json")

if __name__ == "__main__":
    asyncio.run(main())
