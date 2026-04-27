"""Phase 3 LangGraph state definition.

Defines the typed state dictionary that flows through every node in the
Phase 3 cultural localization graph.
"""

from typing import Any, TypedDict

from openai import OpenAI

from core.models import GlobalMetadata


class Phase3State(TypedDict, total=False):
    """Shared state flowing through the Phase 3 LangGraph pipeline.

    Attributes:
        raw_text_pack: Unprocessed text pack from Phase 2 output.
        global_metadata: Validated global metadata with style/constraint info.
        source_pdf_path: Filesystem path to the source PDF.
        use_llm: Whether to invoke the LLM for scoring and translation.
        max_groups: Maximum number of cascading groups for translation.
        client: OpenAI-compatible client instance (or None).
        blocks: Normalized text blocks with unified keys.
        scores: Cultural density scores per block (0-10).
        groups: Chunked groups of block indices with aggregated scores.
        context_established: Running list of previously localized pairs.
        context_safe_pack: Final localized text blocks for API output.
        overflow_warnings: Blocks that exceed bounding-box character limits.
        entity_graph: Entity relationship graph (currently empty placeholder).
        localization_log: Log of localization proposals and decisions.
        images: Localized image replacement metadata.
    """

    # --- Inputs (set once at ingestion) ---
    raw_text_pack: list[dict[str, Any]]
    global_metadata: GlobalMetadata
    source_pdf_path: str
    use_llm: bool
    max_groups: int
    client: OpenAI | None

    # --- Intermediate results (written by nodes) ---
    blocks: list[dict[str, Any]]
    scores: list[int]
    groups: list[dict[str, Any]]
    context_established: list[str]

    # --- Final outputs ---
    context_safe_pack: list[dict[str, Any]]
    overflow_warnings: list[dict[str, Any]]
    entity_graph: dict[str, Any]
    localization_log: list[dict[str, Any]]
    images: list[Any]
