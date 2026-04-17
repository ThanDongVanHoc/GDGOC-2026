"""
OmniLocal Orchestrator — Pipeline State.

Central state schema for the OmniLocal pipeline.
Each Phase reads its inputs from state and writes its outputs back.
The Orchestrator manages this state; Partners never modify it directly.

Design: Phase outputs are stored as opaque blobs (output_phase_N).
The Orchestrator does NOT peek inside — it simply relays them.
"""

from typing import Optional, TypedDict


class OmniLocalState(TypedDict):
    """
    Central pipeline state passed between all LangGraph nodes.

    Convention:
        - Each Phase receives the previous Phase's output blob + global_metadata.
        - Each Phase writes its own output blob (output_phase_N).
        - The Orchestrator treats output blobs as opaque — no peeking inside.
        - global_metadata is extracted from Phase 1's output and stored separately
          because ALL subsequent phases need it.
    """

    # ── Pipeline Control ───────────────────────────────────────
    thread_id: str
    current_phase: int
    status: str  # IDLE | PROCESSING | COMPLETED | FAILED
    pipeline_iteration: int  # QA feedback cycle count (max 2)

    # ── Initial Inputs (from user) ─────────────────────────────
    source_pdf_path: str
    brief_path: str

    # ── Global Metadata (produced by Phase 1, consumed by ALL) ─
    global_metadata: dict

    # ── Phase 0 (Demo Only) ────────────────────────────────────
    camera_image_path: str
    phase0_results: Optional[dict]

    # ── Phase Output Blobs (opaque — Orchestrator doesn't peek) ─
    output_phase_1: Optional[dict]
    output_phase_2: Optional[dict]
    output_phase_3: Optional[dict]
    output_phase_4: Optional[dict]

    # ── Phase 5 Output (QA — tách riêng vì router cần đọc) ────
    qa_status: str  # APPROVED | REJECT_LOCALIZATION
    qa_feedback: Optional[list]
    final_pdf_path: str

    # ── Debug / Tracing ────────────────────────────────────────
    dispatch_info: dict  # Records URL and Payload sent to each phase

