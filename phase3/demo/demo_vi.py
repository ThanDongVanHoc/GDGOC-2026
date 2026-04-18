"""Vietnamese localization validation demo.

Validates a Vietnamese-localized text pack against the original English
source. For each localized entity, computes energy delta to detect
butterfly effects caused by cultural substitutions.

Usage:
    python -m demo.demo_vi

This demo:
    1. Loads both English source and Vietnamese localized text packs
    2. Builds entity graphs for both
    3. Loads ViAMR-v1.0 corpus for cross-lingual scoring
    4. Validates each localization change in the map
    5. Produces a full report with accept/reject decisions
"""

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

from core.butterfly_validator import butterfly_validator
from core.entity_graph import build_entity_graph
from core.models import LocalizationProposal, ValidationStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Paths & Constants
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).parent.parent / "dummy_data"
_EN_PACK_PATH = _DATA_DIR / "verified_text_pack.json"
_VI_PACK_PATH = _DATA_DIR / "verified_text_pack_vi.json"

_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_RESET = "\033[0m"
_DIM = "\033[2m"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> dict:
    """Load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _sep(char: str = "=", n: int = 72) -> None:
    """Print a separator."""
    print(f"\n{char * n}")


def _find_affected_pages(
    entity_name: str, text_pack: dict
) -> list[int]:
    """Find which pages an entity appears on."""
    pages = set()
    for page in text_pack["pages"]:
        for block in page["text_blocks"]:
            for ent in block.get("entities", []):
                if ent["name"] == entity_name:
                    pages.add(page["page_id"])
    return sorted(pages)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_vi_demo() -> None:
    """Run the Vietnamese localization validation demo."""

    _sep()
    print(f"{_BOLD}{_CYAN}")
    print("  Phase 3: Vietnamese Localization Validator")
    print(f"  Butterfly Effect Detection - Cross-Lingual Mode{_RESET}")
    _sep()

    # ── Step 1: Load data ─────────────────────────────────────────────
    print(f"\n{_BOLD}[1/5] Loading text packs...{_RESET}")

    en_pack = _load_json(_EN_PACK_PATH)
    vi_pack = _load_json(_VI_PACK_PATH)
    loc_map = vi_pack["localization_map"]

    print(f"  EN: {en_pack['book_title']} ({en_pack['total_pages']} pages)")
    print(f"  VI: {vi_pack['book_title']} ({vi_pack['total_pages']} pages)")
    print(f"  Localization entries: {len(loc_map)}")

    # ── Step 2: Build entity graphs ───────────────────────────────────
    print(f"\n{_BOLD}[2/5] Building entity graphs...{_RESET}")

    en_graph = build_entity_graph(en_pack)
    vi_graph = build_entity_graph(vi_pack)

    print(f"  EN graph: {len(en_graph)} entities")
    print(f"  VI graph: {len(vi_graph)} entities")

    # Show Vietnamese graph
    print(f"\n  {_CYAN}Vietnamese Entity Graph:{_RESET}")
    for name, node in sorted(vi_graph.items()):
        pages_str = ", ".join(str(p) for p in node["pages"])
        n_related = len(node["related"])
        print(f"    {name} [{node['type']}] pages=[{pages_str}] ({n_related} links)")

    # ── Step 3: Load ViAMR corpus ─────────────────────────────────────
    print(f"\n{_BOLD}[3/5] Loading ViAMR-v1.0 corpus...{_RESET}")

    vi_amr_loaded = False
    try:
        from core.vi_amr_loader import get_index_stats, load_viamr_dataset

        load_viamr_dataset(max_samples=5000)
        stats = get_index_stats()
        vi_amr_loaded = True

        print(f"  {_GREEN}Loaded! {stats['total_graphs']} graphs, "
              f"{stats['unique_concepts']} concepts, "
              f"{stats['unique_relations']} relations{_RESET}")
    except Exception as e:
        print(f"  {_YELLOW}ViAMR unavailable: {e}{_RESET}")

    # ── Step 4: Validate each localization ────────────────────────────
    _sep("-")
    print(f"{_BOLD}{_CYAN}[4/5] Validating localization map{_RESET}")
    _sep("-")

    results = []

    for original, proposed in loc_map.items():
        affected_en = _find_affected_pages(original, en_pack)
        affected_vi = _find_affected_pages(proposed, vi_pack)
        affected = sorted(set(affected_en + affected_vi))

        if not affected:
            affected = [1]

        proposal = LocalizationProposal(
            proposal_id=f"vi_{original.lower().replace(' ', '_')}",
            original=original,
            proposed=proposed,
            affected_pages=affected,
            rationale=f"Cultural localization: {original} -> {proposed}",
        )

        # Base mode
        t0 = time.perf_counter()
        base_result = butterfly_validator(
            proposal=proposal,
            entity_graph=en_graph,
        )
        base_ms = (time.perf_counter() - t0) * 1000

        # Cross-lingual mode
        cl_result = None
        cl_ms = 0.0
        if vi_amr_loaded:
            t0 = time.perf_counter()
            cl_result = butterfly_validator(
                proposal=proposal,
                entity_graph=en_graph,
                use_cross_lingual=True,
            )
            cl_ms = (time.perf_counter() - t0) * 1000

        results.append({
            "original": original,
            "proposed": proposed,
            "pages": affected,
            "base": base_result,
            "base_ms": base_ms,
            "cl": cl_result,
            "cl_ms": cl_ms,
        })

    # ── Print results table ───────────────────────────────────────────
    _sep()
    print(f"{_BOLD}{_CYAN}[5/5] Validation Results{_RESET}")
    _sep()

    # Header
    if vi_amr_loaded:
        print(
            f"\n  {'Entity':<20} {'Localized':<18} "
            f"{'Pages':<12} {'Base dE':>9} {'Base':>8}  "
            f"{'CL dE':>9} {'CL':>8}  {'Diff':>8}"
        )
        print(f"  {'-'*18:<20} {'-'*16:<18} {'-'*10:<12} "
              f"{'-'*9:>9} {'-'*8:>8}  {'-'*9:>9} {'-'*8:>8}  {'-'*8:>8}")
    else:
        print(
            f"\n  {'Entity':<20} {'Localized':<18} "
            f"{'Pages':<12} {'dE':>9} {'Status':>8}"
        )
        print(f"  {'-'*18:<20} {'-'*16:<18} {'-'*10:<12} "
              f"{'-'*9:>9} {'-'*8:>8}")

    total_base_accept = 0
    total_base_reject = 0
    total_cl_accept = 0
    total_cl_reject = 0

    for r in results:
        pages_str = ",".join(str(p) for p in r["pages"][:4])
        if len(r["pages"]) > 4:
            pages_str += "..."

        base_de = r["base"].total_delta_energy
        base_status = r["base"].status.value
        base_color = _GREEN if r["base"].status == ValidationStatus.ACCEPT else _RED

        if r["base"].status == ValidationStatus.ACCEPT:
            total_base_accept += 1
        else:
            total_base_reject += 1

        if vi_amr_loaded and r["cl"] is not None:
            cl_de = r["cl"].total_delta_energy
            cl_status = r["cl"].status.value
            cl_color = _GREEN if r["cl"].status == ValidationStatus.ACCEPT else _RED
            diff = cl_de - base_de
            diff_sign = "+" if diff >= 0 else ""

            if r["cl"].status == ValidationStatus.ACCEPT:
                total_cl_accept += 1
            else:
                total_cl_reject += 1

            print(
                f"  {r['original']:<20} {r['proposed']:<18} "
                f"{pages_str:<12} {base_de:>9.4f} "
                f"{base_color}{base_status:>8}{_RESET}  "
                f"{cl_de:>9.4f} "
                f"{cl_color}{cl_status:>8}{_RESET}  "
                f"{_DIM}{diff_sign}{diff:.4f}{_RESET}"
            )
        else:
            print(
                f"  {r['original']:<20} {r['proposed']:<18} "
                f"{pages_str:<12} {base_de:>9.4f} "
                f"{base_color}{base_status:>8}{_RESET}"
            )

    # ── Conflict details ──────────────────────────────────────────────
    rejected_items = [
        r for r in results
        if r["base"].status == ValidationStatus.REJECT
    ]

    if rejected_items:
        _sep("-")
        print(f"{_BOLD}{_RED}Butterfly Effect Conflicts (Base Mode):{_RESET}")
        _sep("-")
        for r in rejected_items:
            print(f"\n  {_BOLD}{r['original']} -> {r['proposed']}{_RESET}")
            for conflict in r["base"].conflicts:
                print(f"    Entity: {conflict.entity}")
                print(f"    Pages:  {conflict.pages}")
                print(f"    dE:     {conflict.delta_energy:.4f}")
                print(f"    {_DIM}{conflict.reason}{_RESET}")

    # Cross-lingual specific rejections
    if vi_amr_loaded:
        cl_rejected = [
            r for r in results
            if r["cl"] is not None
            and r["cl"].status == ValidationStatus.REJECT
        ]
        if cl_rejected:
            _sep("-")
            print(f"{_BOLD}{_RED}Butterfly Effect Conflicts (Cross-Lingual):{_RESET}")
            _sep("-")
            for r in cl_rejected:
                print(f"\n  {_BOLD}{r['original']} -> {r['proposed']}{_RESET}")
                for conflict in r["cl"].conflicts:
                    print(f"    Entity: {conflict.entity}")
                    print(f"    dE:     {conflict.delta_energy:.4f}")
                    print(f"    {_DIM}{conflict.reason}{_RESET}")

    # ── Summary ───────────────────────────────────────────────────────
    _sep()
    print(f"{_BOLD}Summary{_RESET}")
    _sep()

    avg_base_ms = sum(r["base_ms"] for r in results) / len(results)

    print(f"\n  Total localization entries: {len(results)}")
    print(f"\n  {_BOLD}Base Mode:{_RESET}")
    print(f"    {_GREEN}Accepted: {total_base_accept}{_RESET}")
    print(f"    {_RED}Rejected: {total_base_reject}{_RESET}")
    print(f"    Avg time: {avg_base_ms:.2f} ms")

    if vi_amr_loaded:
        avg_cl_ms = sum(r["cl_ms"] for r in results) / len(results)
        print(f"\n  {_BOLD}Cross-Lingual Mode (ViAMR-enhanced):{_RESET}")
        print(f"    {_GREEN}Accepted: {total_cl_accept}{_RESET}")
        print(f"    {_RED}Rejected: {total_cl_reject}{_RESET}")
        print(f"    Avg time: {avg_cl_ms:.2f} ms")

        # Highlight differences
        diff_items = [
            r for r in results
            if r["cl"] is not None
            and r["base"].status != r["cl"].status
        ]
        if diff_items:
            print(f"\n  {_BOLD}{_YELLOW}Decision changes (Base -> CL):{_RESET}")
            for r in diff_items:
                b = r["base"].status.value
                c = r["cl"].status.value
                print(
                    f"    {r['original']} -> {r['proposed']}: "
                    f"{_RED}{b}{_RESET} -> {_GREEN}{c}{_RESET} "
                    f"(dE: {r['base'].total_delta_energy:.4f} -> "
                    f"{r['cl'].total_delta_energy:.4f})"
                )

    print()


if __name__ == "__main__":
    run_vi_demo()
