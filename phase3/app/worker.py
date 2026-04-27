"""OmniLocal — Phase 3 Worker: Cultural Localization & Butterfly Effect.

LangGraph StateGraph orchestrator. Constructs a four-node pipeline:
    START → normalize → score → translate → finalize → END

The ``run()`` entry-point signature and return shape are unchanged,
so ``app/main.py`` requires zero modifications.
"""

import json
import logging
import os
import time
from typing import Any

from langgraph.graph import END, START, StateGraph
from openai import OpenAI
from dotenv import load_dotenv

# Ensure environment variables (.env) are loaded
load_dotenv()

from app.nodes.finalize import finalize_node
from app.nodes.normalize import normalize_node
from app.nodes.style_detector import detect_style_node
from app.nodes.score import score_node
from app.nodes.translate import translate_node
from app.state import Phase3State
from core.models import GlobalMetadata, Phase3InputPayload

logger = logging.getLogger(__name__)

_FPT_API_KEY: str = os.environ.get("FPT_API_KEY", "")
_FPT_BASE_URL: str = "https://mkp-api.fptcloud.com/v1"

# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def _build_graph() -> StateGraph:
    """Build and return the Phase 3 LangGraph StateGraph.

    The graph defines a linear pipeline of four nodes:
    ``normalize → score → translate → finalize``.

    Returns:
        A compiled LangGraph ``StateGraph`` ready for invocation.
    """
    graph = StateGraph(Phase3State)

    graph.add_node("normalize", normalize_node)
    graph.add_node("detect_style", detect_style_node)
    graph.add_node("score", score_node)
    graph.add_node("translate", translate_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "normalize")
    graph.add_edge("normalize", "detect_style")
    graph.add_edge("detect_style", "score")
    graph.add_edge("score", "translate")
    graph.add_edge("translate", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


# Module-level compiled graph (built once, reused per request)
_COMPILED_GRAPH = _build_graph()

# ---------------------------------------------------------------------------
# Payload ingestion helpers
# ---------------------------------------------------------------------------


def _extract_inputs(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the incoming payload and extract initial state values.

    Args:
        payload: Raw incoming JSON payload from the orchestrator.

    Returns:
        A dict of initial state values for the LangGraph pipeline.
    """
    try:
        validated = Phase3InputPayload(**payload)
        output_phase_2 = validated.output_phase_2 or {}
        if isinstance(output_phase_2, dict):
            raw_text_pack = output_phase_2.get(
                "verified_text_pack",
                validated.verified_text_pack or {},
            )
        else:
            raw_text_pack = validated.verified_text_pack or {}
        source_pdf_path = validated.source_pdf_path
        use_llm = validated.use_llm
        global_metadata = validated.global_metadata
    except Exception as exc:
        logger.error("[Phase3] Payload validation error: %s", exc)
        raw_text_pack = (
            payload.get("output_phase_2", {}).get(
                "verified_text_pack",
                payload.get("verified_text_pack", {}),
            )
        )
        source_pdf_path = payload.get("source_pdf_path", "")
        use_llm = payload.get("use_llm", False)
        global_metadata = GlobalMetadata(
            **payload.get("global_metadata", {})
        )

    # Load cascading config
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "core", "config.json"
    )
    max_groups = 30
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                max_groups = json.load(f).get("cascading_max_groups", 30)
        except Exception:
            pass

    # Build OpenAI-compatible client
    client: OpenAI | None = None
    if use_llm:
        if _FPT_API_KEY:
            client = OpenAI(api_key=_FPT_API_KEY, base_url=_FPT_BASE_URL)
        else:
            logger.warning("[Phase3] use_llm is True but FPT_API_KEY is missing!")

    return {
        "raw_text_pack": raw_text_pack,
        "global_metadata": global_metadata,
        "source_pdf_path": source_pdf_path,
        "use_llm": use_llm,
        "max_groups": max_groups,
        "client": client,
    }


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------


async def run(payload: dict) -> dict:
    """Execute the Phase 3 cultural localization pipeline.

    This is the sole public entry-point consumed by ``app/main.py``.
    The function signature and return schema are identical to the
    previous monolithic implementation.

    Args:
        payload: Raw incoming JSON payload conforming to Phase3InputPayload.

    Returns:
        A dict with ``output_phase_3`` and ``localization_warnings``
        conforming to the Phase 3 API contract.
    """
    t_start = time.perf_counter()

    initial_state = _extract_inputs(payload)
    final_state = await _COMPILED_GRAPH.ainvoke(initial_state)

    elapsed_ms = (time.perf_counter() - t_start) * 1000
    logger.info("[Phase3] Pipeline complete in %.1f ms.", elapsed_ms)

    return {
        "output_phase_3": {
            "context_safe_localized_text_pack": final_state.get(
                "context_safe_pack", []
            ),
            "entity_graph": final_state.get("entity_graph", {}),
            "localization_log": final_state.get("localization_log", []),
            "Images": final_state.get("images", []),
            "source_pdf_path": initial_state["source_pdf_path"],
        },
        "localization_warnings": final_state.get("overflow_warnings", []),
    }
