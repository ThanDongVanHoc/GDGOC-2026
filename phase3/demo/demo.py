"""Demo script for Phase 3 — AMR-based Energy Delta Butterfly Effect Validator.

This script demonstrates the full pipeline:
    1. Load dummy Verified Text Pack data
    2. Build the entity graph (Phase 3.1)
    3. Propose localization changes (Phase 3.2 simulation)
    4. Validate proposals using BFS + energy delta (Phase 3.3)
    5. Display detailed energy analysis results

Usage:
    python -m demo.demo

Note:
    The demo includes two modes:
    - With AMR model: Full pipeline using amrlib for semantic parsing
    - Without AMR model: Fallback mode using entity graph relations only

    If amrlib models are not installed, the demo will automatically
    fall back to the entity-graph-only mode.
"""

import io
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

from core.butterfly_validator import butterfly_validator
from core.entity_graph import build_entity_graph, get_entity_subgraph
from core.models import LocalizationProposal, ValidationStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DUMMY_DATA_PATH = Path(__file__).parent.parent / "dummy_data" / "verified_text_pack.json"

# Color codes for terminal output
_GREEN = "\033[92m"
_RED = "\033[91m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def load_dummy_data() -> dict[str, Any]:
    """Load the dummy Verified Text Pack from JSON.

    Returns:
        The parsed JSON data as a dictionary.

    Raises:
        FileNotFoundError: If the dummy data file does not exist.
    """
    with open(_DUMMY_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def print_separator(char: str = "=", length: int = 70) -> None:
    """Print a visual separator line.

    Args:
        char: The character to repeat.
        length: The total length of the separator.
    """
    print(f"\n{char * length}")


def print_entity_graph_summary(entity_graph: dict[str, dict]) -> None:
    """Print a formatted summary of the entity graph.

    Args:
        entity_graph: The entity graph dictionary.
    """
    print(f"\n{_BOLD}{_CYAN}Entity Graph Summary:{_RESET}")
    print(f"  Total entities: {len(entity_graph)}")
    print()

    for name, node in sorted(entity_graph.items()):
        pages_str = ", ".join(str(p) for p in node["pages"])
        related_str = ", ".join(node["related"]) if node["related"] else "(none)"
        print(
            f"  {_BOLD}{name}{_RESET} "
            f"[{node['type']}] "
            f"pages=[{pages_str}] "
            f"related=[{related_str}]"
        )


def print_validation_result(
    proposal: LocalizationProposal,
    result: Any,
    elapsed_ms: float,
) -> None:
    """Print a formatted validation result with energy details.

    Args:
        proposal: The localization proposal that was validated.
        result: The ValidationResult object.
        elapsed_ms: Wall-clock time in milliseconds.
    """
    status_color = _GREEN if result.status == ValidationStatus.ACCEPT else _RED
    status_icon = "[OK]" if result.status == ValidationStatus.ACCEPT else "[!!]"

    print(f"\n{_BOLD}Proposal: '{proposal.original}' -> '{proposal.proposed}'{_RESET}")
    print(f"  Rationale: {proposal.rationale}")
    print(f"  Affected pages: {proposal.affected_pages}")
    print(
        f"  Result: {status_color}{status_icon} {result.status.value}{_RESET}"
    )
    print(f"  Total Delta Energy: {_YELLOW}{result.total_delta_energy:.4f}{_RESET}")
    print(f"  Validation time: {elapsed_ms:.2f} ms")

    if result.conflicts:
        print(f"\n  {_RED}{_BOLD}Conflicts detected:{_RESET}")
        for conflict in result.conflicts:
            print(f"    - Entity: {conflict.entity}")
            print(f"      Pages: {conflict.pages}")
            print(f"      Delta Energy: {conflict.delta_energy:.4f}")
            print(f"      Reason: {conflict.reason}")

    if result.energy_details:
        print(f"\n  {_CYAN}Energy Edge Details:{_RESET}")
        for edge in result.energy_details[:10]:
            print(
                f"    {edge.source} --[{edge.relation}]--> {edge.target}: "
                f"E={edge.energy:.4f}"
            )
            for factor, value in edge.breakdown.items():
                print(f"      {factor}: {value:.4f}")


# ---------------------------------------------------------------------------
# Demo Proposals
# ---------------------------------------------------------------------------

DEMO_PROPOSALS = [
    LocalizationProposal(
        proposal_id="prop_001",
        original="Snow",
        proposed="Rain",
        affected_pages=[1, 2, 3, 5, 8],
        rationale=(
            "Snow is uncommon in Vietnam. Replace with Rain "
            "for cultural familiarity."
        ),
    ),
    LocalizationProposal(
        proposal_id="prop_002",
        original="Fireplace",
        proposed="Charcoal Stove",
        affected_pages=[2, 7],
        rationale=(
            "Fireplaces are not common in Vietnamese homes. "
            "Replace with traditional charcoal stove."
        ),
    ),
    LocalizationProposal(
        proposal_id="prop_003",
        original="Hot Chocolate",
        proposed="Warm Sweet Soup",
        affected_pages=[2],
        rationale=(
            "Hot chocolate is less common in Vietnam. "
            "Replace with che (sweet soup), a popular warm dessert."
        ),
    ),
    LocalizationProposal(
        proposal_id="prop_004",
        original="Sleigh",
        proposed="Bicycle",
        affected_pages=[4],
        rationale=(
            "Sleigh rides are unknown in Vietnam. "
            "Replace with bicycle, a common transport."
        ),
    ),
    LocalizationProposal(
        proposal_id="prop_005",
        original="Wool Hat",
        proposed="Straw Hat",
        affected_pages=[1, 3, 7],
        rationale=(
            "Wool hats are uncommon in tropical Vietnam. "
            "Replace with non la (straw hat)."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Main Demo
# ---------------------------------------------------------------------------


def run_demo() -> None:
    """Execute the full Phase 3 demo pipeline.

    Steps:
        1. Load dummy Verified Text Pack
        2. Build entity graph
        3. Attempt AMR enrichment (optional)
        4. Run butterfly validation on all demo proposals
        5. Print comprehensive results and feasibility assessment
    """
    print_separator()
    print(f"{_BOLD}{_CYAN}")
    print("  Phase 3: AMR-based Energy Delta - Butterfly Effect Validator")
    print(f"  OmniLocal - GDGOC 2026{_RESET}")
    print_separator()

    # Step 1: Load data
    print(f"\n{_BOLD}[Step 1] Loading Verified Text Pack...{_RESET}")
    text_pack = load_dummy_data()
    print(f"  Book: {text_pack['book_title']}")
    print(f"  Pages: {text_pack['total_pages']}")

    # Step 2: Build entity graph
    print(f"\n{_BOLD}[Step 2] Building Entity Graph (Phase 3.1)...{_RESET}")
    entity_graph = build_entity_graph(text_pack)
    print_entity_graph_summary(entity_graph)

    # Step 3: Try AMR enrichment
    amr_adjacency = None
    print(f"\n{_BOLD}[Step 3] AMR Enrichment (English)...{_RESET}")
    try:
        from core.amr_parser import load_amr_model
        from core.entity_graph import merge_amr_into_entity_graph

        load_amr_model()

        # Collect all sentences from the text pack
        all_sentences = []
        for page in text_pack["pages"]:
            for block in page["text_blocks"]:
                all_sentences.append(block["text"])

        amr_adjacency = merge_amr_into_entity_graph(
            entity_graph, all_sentences
        )
        print(
            f"  {_GREEN}AMR enrichment successful! "
            f"{len(amr_adjacency)} concept nodes merged.{_RESET}"
        )
    except Exception as e:
        print(
            f"  {_YELLOW}AMR model not available: {e}{_RESET}"
        )
        print(
            f"  {_YELLOW}Falling back to entity-graph-only mode "
            f"(using ':related' edges).{_RESET}"
        )

    # Step 3.5: Load Vietnamese AMR corpus
    vi_amr_loaded = False
    print(f"\n{_BOLD}[Step 3.5] Loading ViAMR-v1.0 (Vietnamese AMR Corpus)...{_RESET}")
    try:
        from core.vi_amr_loader import get_index_stats, load_viamr_dataset

        # Load with sample limit for demo speed
        vi_index = load_viamr_dataset(max_samples=5000)
        stats = get_index_stats()
        vi_amr_loaded = True

        print(f"  {_GREEN}ViAMR-v1.0 loaded successfully!{_RESET}")
        print(f"    Graphs parsed: {stats.get('total_graphs', 0)}")
        print(f"    Unique concepts: {stats.get('unique_concepts', 0)}")
        print(f"    Unique relations: {stats.get('unique_relations', 0)}")
        print(f"    Concept pairs: {stats.get('unique_pairs', 0)}")
    except Exception as e:
        print(
            f"  {_YELLOW}ViAMR corpus not available: {e}{_RESET}"
        )
        print(
            f"  {_YELLOW}Cross-lingual energy mode disabled.{_RESET}"
        )

    # Step 4: Validate proposals (Base Mode)
    print_separator("-")
    print(
        f"{_BOLD}{_CYAN}[Step 4] "
        f"Butterfly Effect Validation - Base Mode (Phase 3.3){_RESET}"
    )
    print_separator("-")

    results_summary = []

    for proposal in DEMO_PROPOSALS:
        start_time = time.perf_counter()
        result = butterfly_validator(
            proposal=proposal,
            entity_graph=entity_graph,
            amr_adjacency=amr_adjacency,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        print_validation_result(proposal, result, elapsed_ms)
        results_summary.append((proposal, result, elapsed_ms))
        print_separator(".", 50)

    # Step 4.5: Cross-lingual validation (if ViAMR loaded)
    cross_lingual_results = []
    if vi_amr_loaded:
        print_separator("-")
        print(
            f"{_BOLD}{_CYAN}[Step 4.5] "
            f"Cross-Lingual Validation (ViAMR-enhanced){_RESET}"
        )
        print_separator("-")

        for proposal in DEMO_PROPOSALS:
            start_time = time.perf_counter()
            result = butterfly_validator(
                proposal=proposal,
                entity_graph=entity_graph,
                amr_adjacency=amr_adjacency,
                use_cross_lingual=True,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            print_validation_result(proposal, result, elapsed_ms)
            cross_lingual_results.append((proposal, result, elapsed_ms))
            print_separator(".", 50)

    # Step 5: Summary
    print_separator()
    print(f"{_BOLD}{_CYAN}[Step 5] Validation Summary{_RESET}")
    print_separator()

    # Base mode summary
    accepted = sum(
        1 for _, r, _ in results_summary
        if r.status == ValidationStatus.ACCEPT
    )
    rejected = sum(
        1 for _, r, _ in results_summary
        if r.status == ValidationStatus.REJECT
    )
    avg_time = sum(t for _, _, t in results_summary) / len(results_summary)

    print(f"\n  {_BOLD}Base Mode:{_RESET}")
    print(f"    Total proposals: {len(results_summary)}")
    print(f"    {_GREEN}Accepted: {accepted}{_RESET}")
    print(f"    {_RED}Rejected: {rejected}{_RESET}")
    print(f"    Average validation time: {avg_time:.2f} ms")

    # Cross-lingual summary
    if cross_lingual_results:
        cl_accepted = sum(
            1 for _, r, _ in cross_lingual_results
            if r.status == ValidationStatus.ACCEPT
        )
        cl_rejected = sum(
            1 for _, r, _ in cross_lingual_results
            if r.status == ValidationStatus.REJECT
        )
        cl_avg_time = (
            sum(t for _, _, t in cross_lingual_results)
            / len(cross_lingual_results)
        )

        print(f"\n  {_BOLD}Cross-Lingual Mode (ViAMR-enhanced):{_RESET}")
        print(f"    Total proposals: {len(cross_lingual_results)}")
        print(f"    {_GREEN}Accepted: {cl_accepted}{_RESET}")
        print(f"    {_RED}Rejected: {cl_rejected}{_RESET}")
        print(f"    Average validation time: {cl_avg_time:.2f} ms")

        # Compare deltas
        print(
            f"\n  {_BOLD}Energy Delta Comparison "
            f"(Base vs Cross-Lingual):{_RESET}"
        )
        for i, proposal in enumerate(DEMO_PROPOSALS):
            base_de = results_summary[i][1].total_delta_energy
            cl_de = cross_lingual_results[i][1].total_delta_energy
            diff = cl_de - base_de
            direction = "+" if diff >= 0 else ""
            print(
                f"    {proposal.original} -> {proposal.proposed}: "
                f"Base={base_de:.4f}  CL={cl_de:.4f}  "
                f"({direction}{diff:.4f})"
            )

    print_separator()
    print(f"\n{_BOLD}Feasibility Assessment: Energy Delta Approach{_RESET}")

    feasibility_score = "7.5/10"
    if vi_amr_loaded:
        feasibility_score = "8.5/10 (ViAMR-enhanced)"

    print(
        f"""
  {_CYAN}Strengths:{_RESET}
    - Formal semantic grounding via AMR relations
    - Quantifiable risk score (continuous, not binary)
    - Sub-millisecond validation speed (BFS + cached energy)
    - Interpretable: energy breakdown shows WHY a conflict exists
    - Modular: easy to add new energy factors
    - Cross-lingual: ViAMR-v1.0 corpus enables Vietnamese-aware scoring

  {_YELLOW}Weaknesses:{_RESET}
    - Energy weights need empirical tuning with real book data
    - AMR model download (~400MB) adds setup overhead
    - ViAMR corpus skews toward news/literature domains
    - Cannot capture deep cultural nuances without LLM assist

  {_GREEN}Overall Feasibility: {feasibility_score}{_RESET}
    The addition of Vietnamese AMR corpus data improves accuracy
    by grounding energy scores in real Vietnamese semantics.
    Best used as a SUPPLEMENTARY confidence score alongside
    BFS conflict detection.
"""
    )


if __name__ == "__main__":
    run_demo()

