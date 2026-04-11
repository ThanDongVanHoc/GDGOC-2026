"""
OmniLocal Orchestrator — Pipeline State.

Central state schema for the OmniLocal pipeline.
Each Phase reads its inputs from state and writes its outputs back.
The Orchestrator manages this state; Partners never modify it directly.
"""

from typing import Optional, TypedDict


class OmniLocalState(TypedDict):
    """
    Central pipeline state passed between all LangGraph nodes.

    Convention:
        - Each Phase reads fields written by the previous Phase.
        - Each Phase writes its own output fields.
        - Internal Partner state is NOT stored here.
    """

    # ── Pipeline Control ───────────────────────────────────────
    thread_id: str
    current_phase: int
    status: str  # IDLE | PROCESSING | COMPLETED | FAILED
    pipeline_iteration: int  # QA feedback cycle count (max 2)

    # ── Initial Inputs ─────────────────────────────────────────
    source_pdf_path: str
    brief_path: str

    # ── Phase 0 Outputs (Demo Only) ────────────────────────────
    camera_image_path: str
    phase0_results: Optional[dict]

    # ── Phase 1 → Phase 2 ─────────────────────────────────────
    global_metadata: dict
    standardized_pack: list[dict]

    # ── Phase 2 → Phase 3 ─────────────────────────────────────
    verified_text_pack: list[dict]
    translation_warnings: list[dict]

    # ── Phase 3 → Phase 4 ─────────────────────────────────────
    localized_text_pack: list[dict]
    localization_log: list[dict]

    # ── Phase 4 → Phase 5 ─────────────────────────────────────
    composited_pdf_path: str

    # ── Phase 5 Output ─────────────────────────────────────────
    qa_status: str
    qa_feedback: Optional[dict]
    final_pdf_path: str
