"""Phase 3 — Complete End-to-End Workflow.

Standalone script that exercises the full Phase 3 pipeline:
    1. Load orchestrator payload (API contract format)
    2. Run Task #p3.1 (Entity Graph + AMR) in parallel
    3. Run Task #p3.2 (LLM Localization Agent)
    4. Run Task #p3.3 (Butterfly Validator — parallel)
    5. Run Task #p3.4 (Mutation + Serialization)
    6. Validate output against API contract schema
    7. Write results to phase3/output/

Usage:
    python run_workflow.py                  # Deterministic fallback mode
    python run_workflow.py --use-llm        # LLM mode (FPT Marketplace)
"""

import argparse
import asyncio
import io
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

from app.worker import run as run_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_workflow")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PAYLOAD_PATH = Path(__file__).parent / "dummy_data" / "orchestrator_payload.json"
_OUTPUT_DIR = Path(__file__).parent / "output"

# Colors
_G = "\033[92m"
_R = "\033[91m"
_Y = "\033[93m"
_C = "\033[96m"
_B = "\033[1m"
_D = "\033[2m"
_RST = "\033[0m"


# ---------------------------------------------------------------------------
# API Contract schema validation
# ---------------------------------------------------------------------------

_REQUIRED_SAFE_BLOCK_KEYS = {
    "original_content", "localized_content", "bbox", "page_id",
    "source_type", "font", "size", "color", "flags", "warning",
}

_REQUIRED_LOG_KEYS = {
    "proposal_id", "original", "proposed", "affected_pages",
    "rationale", "status", "conflicts",
}

_REQUIRED_WARNING_KEYS = {
    "page_id", "block_index", "original_content", "localized_content",
    "max_estimated_chars", "actual_chars", "overflow_ratio",
}


def _validate_contract(result: dict) -> list[str]:
    """Validate the worker output against the API contract schema.

    Args:
        result: The output dict from run_worker().

    Returns:
        List of validation error strings. Empty means valid.
    """
    errors: list[str] = []

    # Check top-level keys
    if "output_phase_3" not in result:
        errors.append("Missing key: output_phase_3")
        return errors

    p3 = result["output_phase_3"]

    if "context_safe_localized_text_pack" not in p3:
        errors.append("Missing: output_phase_3.context_safe_localized_text_pack")
    if "entity_graph" not in p3:
        errors.append("Missing: output_phase_3.entity_graph")
    if "localization_log" not in p3:
        errors.append("Missing: output_phase_3.localization_log")

    if "localization_warnings" not in result:
        errors.append("Missing key: localization_warnings")

    # Validate safe blocks
    for i, block in enumerate(p3.get("context_safe_localized_text_pack", [])):
        missing = _REQUIRED_SAFE_BLOCK_KEYS - set(block.keys())
        if missing:
            errors.append(f"Safe block [{i}] missing keys: {missing}")

    # Validate log entries
    for i, entry in enumerate(p3.get("localization_log", [])):
        missing = _REQUIRED_LOG_KEYS - set(entry.keys())
        if missing:
            errors.append(f"Log entry [{i}] missing keys: {missing}")

    # Validate warnings
    for i, warn in enumerate(result.get("localization_warnings", [])):
        missing = _REQUIRED_WARNING_KEYS - set(warn.keys())
        if missing:
            errors.append(f"Warning [{i}] missing keys: {missing}")

    return errors


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

async def main() -> None:
    """Run the complete Phase 3 workflow."""
    parser = argparse.ArgumentParser(
        description="Phase 3 — Complete Workflow Demo"
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable LLM-based proposal generation (FPT Marketplace)",
    )
    args = parser.parse_args()

    print(f"\n{'=' * 72}")
    print(f"{_B}{_C}")
    print(f"  OmniLocal — Phase 3: Complete Workflow")
    print(f"  Cultural Localization & Butterfly Effect Pipeline")
    print(f"{_RST}")
    print(f"{'=' * 72}")

    mode_str = f"{_G}LLM (FPT Marketplace / gemma-4-31B-it){_RST}" if args.use_llm \
        else f"{_Y}Deterministic Fallback{_RST}"
    print(f"\n  Mode: {mode_str}")

    # ── Step 1: Load payload ──────────────────────────────────────
    print(f"\n{_B}[1/6] Loading orchestrator payload...{_RST}")
    with open(_PAYLOAD_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)

    payload["use_llm"] = args.use_llm

    thread_id = payload["thread_id"]
    text_pack = payload["output_phase_2"]["verified_text_pack"]
    metadata = payload["global_metadata"]

    print(f"  Thread ID: {thread_id}")
    print(f"  Book: {text_pack.get('book_title', 'Unknown')}")
    print(f"  Pages: {text_pack.get('total_pages', 0)}")
    print(f"  Target: {metadata.get('target_language', '?')}")
    print(f"  Protected names: {metadata.get('protected_names', [])}")
    print(f"  Locked rules: {len(metadata.get('never_change_rules', []))}")

    # ── Step 2-5: Run worker ──────────────────────────────────────
    print(f"\n{_B}[2/6] Running Phase 3 worker pipeline...{_RST}")
    print(f"  {_D}(Tasks p3.1 + p3.2 + p3.3 + p3.4 with parallel execution){_RST}")

    t_start = time.perf_counter()
    result = await run_worker(payload)
    elapsed = (time.perf_counter() - t_start) * 1000

    print(f"\n  {_G}Pipeline complete in {elapsed:.0f} ms{_RST}")

    # ── Step 3: Display results ───────────────────────────────────
    p3_out = result["output_phase_3"]
    safe_pack = p3_out["context_safe_localized_text_pack"]
    entity_graph = p3_out["entity_graph"]
    loc_log = p3_out["localization_log"]
    warnings = result["localization_warnings"]

    print(f"\n{_B}[3/6] Results Summary{_RST}")
    print(f"{'─' * 72}")

    # Entity graph
    print(f"\n  {_C}Entity Graph:{_RST} {len(entity_graph)} entities")
    for name, node in sorted(entity_graph.items()):
        pages = node.get("pages", [])
        n_rel = len(node.get("related", []))
        print(f"    {name} [{node.get('type', '?')}] pages={pages} ({n_rel} links)")

    # Localization log
    print(f"\n  {_C}Localization Log:{_RST} {len(loc_log)} entries")
    print(f"\n  {'Entity':<18} {'Proposed':<18} {'Status':<15} {'ΔE':>8}")
    print(f"  {'─'*17:<18} {'─'*16:<18} {'─'*13:<15} {'─'*8:>8}")

    n_accept = 0
    n_reject = 0
    n_locked = 0

    for entry in loc_log:
        status = entry["status"]
        de = entry.get("delta_energy", 0.0)

        if status == "ACCEPT":
            color = _G
            n_accept += 1
        elif status == "REJECT_LOCKED":
            color = _Y
            n_locked += 1
        else:
            color = _R
            n_reject += 1

        print(
            f"  {entry['original']:<18} {entry['proposed']:<18} "
            f"{color}{status:<15}{_RST} {de:>8.4f}"
        )

    print(f"\n  Totals: {_G}{n_accept} accepted{_RST} | "
          f"{_R}{n_reject} rejected{_RST} | "
          f"{_Y}{n_locked} locked{_RST}")

    # Safe text pack
    print(f"\n  {_C}Context-Safe Text Pack:{_RST} {len(safe_pack)} blocks")
    changed_blocks = [
        b for b in safe_pack
        if b["original_content"] != b["localized_content"]
    ]
    if changed_blocks:
        print(f"  Changed blocks: {len(changed_blocks)}")
        for b in changed_blocks[:5]:
            print(f"    p{b['page_id']}: \"{b['original_content'][:50]}...\"")
            print(f"         -> \"{b['localized_content'][:50]}...\"")

    # Overflow warnings
    if warnings:
        print(f"\n  {_Y}Overflow Warnings:{_RST} {len(warnings)}")
        for w in warnings:
            print(
                f"    p{w['page_id']} block[{w['block_index']}]: "
                f"{w['actual_chars']} chars > {w['max_estimated_chars']} max "
                f"(ratio: {w['overflow_ratio']}x)"
            )
    else:
        print(f"\n  {_G}No overflow warnings.{_RST}")

    # ── Step 4: Conflict details ──────────────────────────────────
    conflicts = [e for e in loc_log if e["status"] == "REJECT"]
    if conflicts:
        print(f"\n{_B}[4/6] Butterfly Effect Conflicts{_RST}")
        print(f"{'─' * 72}")
        for entry in conflicts:
            print(f"\n  {_R}{entry['original']} -> {entry['proposed']}{_RST}")
            for c in entry.get("conflicts", []):
                print(f"    Entity: {c.get('entity', '?')}")
                print(f"    ΔE:     {c.get('delta_energy', 0):.4f}")
                print(f"    {_D}{c.get('reason', '')}{_RST}")
    else:
        print(f"\n{_B}[4/6]{_RST} No butterfly conflicts detected.")

    # ── Step 5: Validate API contract ─────────────────────────────
    print(f"\n{_B}[5/6] API Contract Validation{_RST}")
    print(f"{'─' * 72}")

    errors = _validate_contract(result)
    if errors:
        print(f"\n  {_R}FAILED — {len(errors)} contract violations:{_RST}")
        for err in errors:
            print(f"    ✗ {err}")
    else:
        print(f"\n  {_G}✓ Output matches API_CONTRACT.md Phase 3 schema{_RST}")
        print(f"    - context_safe_localized_text_pack: {len(safe_pack)} blocks")
        print(f"    - entity_graph: {len(entity_graph)} entities")
        print(f"    - localization_log: {len(loc_log)} entries")
        print(f"    - localization_warnings: {len(warnings)} warnings")

    # ── Step 6: Write output ──────────────────────────────────────
    print(f"\n{_B}[6/6] Writing output files{_RST}")
    print(f"{'─' * 72}")

    _OUTPUT_DIR.mkdir(exist_ok=True)

    result_path = _OUTPUT_DIR / "result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  {_G}✓{_RST} {result_path}")

    log_path = _OUTPUT_DIR / "localization_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(loc_log, f, indent=2, ensure_ascii=False)
    print(f"  {_G}✓{_RST} {log_path}")

    # Write entity graph separately for inspection
    graph_path = _OUTPUT_DIR / "entity_graph.json"
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(entity_graph, f, indent=2, ensure_ascii=False)
    print(f"  {_G}✓{_RST} {graph_path}")

    print(f"\n{'=' * 72}")
    print(f"{_B}{_G}  Phase 3 workflow complete!{_RST}")
    print(f"  Total time: {elapsed:.0f} ms")
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    asyncio.run(main())
