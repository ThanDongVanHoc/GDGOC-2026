"""End-to-end test for Phase 3 worker using real Phase 1 & 2 data.

Loads the actual output payloads from dummy_data/ and constructs
the Orchestrator payload that Phase 3 would receive at runtime.
Exercises the new LangGraph-based cascading pipeline nodes.
"""

import asyncio
import json
import logging
import os
import sys

from dotenv import load_dotenv

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app.worker import run  # noqa: E402

# Paths to real data files
_DATA_DIR = os.path.join(os.path.dirname(__file__), "dummy_data")
_PHASE1_PATH = os.path.join(_DATA_DIR, "phase1_result.json")
_PHASE2_PATH = os.path.join(_DATA_DIR, "phase2_result.json")


def _load_json(path: str) -> dict:
    """Helper to load JSON from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_payload() -> dict:
    """Build the Orchestrator payload that Phase 3 would receive.

    Matches the API contract:
        thread_id, webhook_url, global_metadata,
        output_phase_1 (standardized_pack from Phase 1),
        output_phase_2 (verified_text_pack + translation_warnings from Phase 2).
    """
    phase1 = _load_json(_PHASE1_PATH)
    phase2 = _load_json(_PHASE2_PATH)

    phase1_result = phase1.get("result", phase1)
    phase2_result = phase2.get("result", phase2)

    # Ensure we exercise the new style-aware logic
    metadata = phase1_result.get("global_metadata", {})
    if "style_register" not in metadata:
        # Default to children_book to test aggressive localization
        metadata["style_register"] = "children_book"
    if "target_age_tone" not in metadata:
        metadata["target_age_tone"] = 8

    return {
        "thread_id": phase1.get("thread_id", "test-real-data"),
        "webhook_url": "http://localhost:8003/webhook/test",
        "global_metadata": metadata,
        "output_phase_1": phase1_result.get("standardized_pack", []),
        "output_phase_2": {
            "verified_text_pack": phase2_result.get("verified_text_pack", []),
            "translation_warnings": phase2_result.get(
                "translation_warnings", []
            ),
        },
        "source_pdf_path": os.path.join(
            os.path.dirname(__file__), "data", "uploads", "source.pdf"
        ),
        "use_llm": True,
    }


async def main():
    """Main test execution entry-point."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s",
    )
    # Ensure UTF-8 output for Vietnamese characters
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    payload = _build_payload()

    pages_count = len(payload["output_phase_1"])
    text_blocks_count = len(
        payload["output_phase_2"].get("verified_text_pack", [])
    )
    image_blocks_count = sum(
        len(p.get("image_blocks", []))
        for p in payload["output_phase_1"]
    )

    print(f"Loaded real data: {pages_count} pages, "
          f"{text_blocks_count} text blocks, "
          f"{image_blocks_count} image blocks")
    print(f"Target Style: {payload['global_metadata']['style_register']}")
    print("Running Phase 3 worker (LangGraph Pipeline)...")

    try:
        # Load .env for API keys
        load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
        
        result = await run(payload)

        # Write result to file for inspection
        output_path = os.path.join(_DATA_DIR, "phase3_result.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\nResult written to: {output_path}")

        # Print summary
        output = result.get("output_phase_3", {})
        warnings = result.get("localization_warnings", [])
        log = output.get("localization_log", [])
        graph = output.get("entity_graph", {})
        safe_pack = output.get("context_safe_localized_text_pack", [])
        images = output.get("Images", [])

        print(f"\n--- Phase 3 Execution Summary ---")
        print(f"Entity graph nodes: {len(graph)}")
        print(f"Localization proposals: {len(log)}")
        accepted = sum(1 for e in log if e.get("status") == "ACCEPT")
        rejected = sum(1 for e in log if "REJECT" in e.get("status", ""))
        print(f"  Accepted: {accepted}, Rejected: {rejected}")
        print(f"Safe text blocks localized: {len(safe_pack)}")
        print(f"Images processed: {len(images)}")
        print(f"Overflow warnings: {len(warnings)}")

        if graph:
            print(f"\nEntity graph sample (first 5):")
            for i, (name, node) in enumerate(graph.items()):
                if i >= 5:
                    break
                pages = node.get("pages", [])
                related = node.get("related", [])
                print(f"  {name} ({node.get('type')}) "
                      f"| pages: {pages} | related: {related}")
    
    except Exception as exc:
        print(f"\n[ERROR] Worker execution failed: {type(exc).__name__}: {exc}")
        print("\nNOTE: Ensure langgraph, pydantic, and openai are installed in your environment.")
        print("For local logic verification in MSYS2/MinGW, use 'python verify_prompt_logic.py'.")


if __name__ == "__main__":
    asyncio.run(main())
