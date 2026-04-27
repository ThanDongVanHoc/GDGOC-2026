"""Normalize node — flattens and standardizes the raw text pack.

Converts the heterogeneous text pack formats (nested pages or flat list)
into a uniform list of block dictionaries with canonical keys.
"""

import logging
from typing import Any

from app.state import Phase3State

logger = logging.getLogger(__name__)


def _normalize_text_pack(raw_text_pack: Any) -> list[dict[str, Any]]:
    """Return a flat list of text blocks with normalized keys.

    Handles two input shapes:
    1. ``{"pages": [{"page_id": ..., "text_blocks": [...]}]}``  (nested)
    2. ``[{"page_id": ..., "translated_content": ...}]``         (flat)

    Args:
        raw_text_pack: Raw text pack from Phase 2 output.

    Returns:
        A list of dicts, each with canonical keys: ``original_content``,
        ``english_content``, ``translated_content``, ``bbox``, ``page_id``,
        ``source_type``, ``font``, ``size``, ``color``, ``flags``,
        ``warning``, and ``localized_content``.
    """
    blocks: list[dict[str, Any]] = []

    if isinstance(raw_text_pack, dict) and "pages" in raw_text_pack:
        for page in raw_text_pack["pages"]:
            pid = page.get("page_id", 0)
            for block in page.get("text_blocks", []):
                block["page_id"] = pid
                blocks.append(block)
    elif isinstance(raw_text_pack, list):
        for block in raw_text_pack:
            blocks.append(block)

    normalized: list[dict[str, Any]] = []
    for block in blocks:
        # Use a more robust mapping for Phase 2 outputs
        original = block.get("original_content", block.get("text", ""))
        translated = block.get("translated_content", "")
        
        normalized.append({
            "original_content": original,
            "english_content": original,
            "translated_content": translated,
            "bbox": block.get("bbox", [0.0, 0.0, 0.0, 0.0]),
            "page_id": block.get("page_id", 1),
            "source_type": block.get("source_type", "text"),
            "font": block.get("font", ""),
            "size": block.get("size", 0.0),
            "color": block.get("color", 0),
            "flags": block.get("flags", 0),
            "warning": block.get("warning", None),
            "localized_content": "",
        })
    return normalized


def normalize_node(state: Phase3State) -> dict[str, Any]:
    """LangGraph node: normalize the raw text pack into canonical blocks.

    Reads:
        ``state["raw_text_pack"]``

    Writes:
        ``blocks`` — list of normalized block dicts.

    Args:
        state: Current graph state.

    Returns:
        Partial state update with ``blocks``.
    """
    raw = state.get("raw_text_pack", [])
    blocks = _normalize_text_pack(raw)
    logger.info("[Phase3:Normalize] Produced %d normalized blocks.", len(blocks))
    return {"blocks": blocks}
