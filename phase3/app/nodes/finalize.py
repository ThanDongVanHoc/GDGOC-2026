"""Finalize node — overflow detection and output pack assembly.

Checks each localized block against its bounding-box character capacity
and assembles the final ``context_safe_localized_text_pack`` and
``localization_warnings`` payloads conforming to the API contract.
"""

import logging
import math
from typing import Any

from app.state import Phase3State

logger = logging.getLogger(__name__)

_DEFAULT_CHAR_WIDTH_RATIO: float = 0.55
_LINE_HEIGHT_FACTOR: float = 1.2


def _estimate_max_chars(bbox: list[float], font_size: float) -> int:
    """Estimate maximum character capacity for a bounding box.

    Uses a simple mono-space approximation: characters per line × number
    of lines that fit vertically.

    Args:
        bbox: Bounding box as ``[x0, y0, x1, y1]``.
        font_size: Font size in points.

    Returns:
        Estimated maximum number of characters, or 10 000 as a fallback.
    """
    max_chars = 10_000
    if len(bbox) == 4 and font_size > 0:
        bw = abs(bbox[2] - bbox[0])
        bh = abs(bbox[3] - bbox[1])
        cw = font_size * _DEFAULT_CHAR_WIDTH_RATIO
        lh = font_size * _LINE_HEIGHT_FACTOR
        if bw > 0 and bh > 0 and cw > 0:
            chars_per_line = max(1, math.floor(bw / cw))
            num_lines = max(1, math.floor(bh / lh))
            max_chars = max(1, chars_per_line * num_lines)
    return max_chars


def finalize_node(state: Phase3State) -> dict[str, Any]:
    """LangGraph node: assemble the final output pack with overflow warnings.

    Reads:
        ``state["blocks"]``

    Writes:
        ``context_safe_pack`` — API-contract-compliant localized text pack.
        ``overflow_warnings`` — blocks exceeding bounding-box capacity.

    Args:
        state: Current graph state.

    Returns:
        Partial state update with ``context_safe_pack`` and
        ``overflow_warnings``.
    """
    blocks = state.get("blocks", [])
    context_safe_pack: list[dict[str, Any]] = []
    overflow_warnings: list[dict[str, Any]] = []

    for i, block in enumerate(blocks):
        bbox = block["bbox"]
        font_size = block["size"]
        max_chars = _estimate_max_chars(bbox, font_size)

        loc_text = block["localized_content"]
        if len(loc_text) > max_chars:
            overflow_warnings.append({
                "page_id": block["page_id"],
                "block_index": i,
                "original_content": block["original_content"],
                "raw_translate_content": block["translated_content"],
                "localized_content": loc_text,
                "max_estimated_chars": max_chars,
                "actual_chars": len(loc_text),
                "overflow_ratio": round(len(loc_text) / max_chars, 2),
            })

        context_safe_pack.append({
            "original_content": block["original_content"],
            "raw_translate_content": block["translated_content"],
            "localized_content": loc_text,
            "bbox": block["bbox"],
            "page_id": block["page_id"],
            "source_type": block["source_type"],
            "font": block["font"],
            "size": block["size"],
            "color": block["color"],
            "flags": block["flags"],
            "warning": block["warning"],
        })

    logger.info(
        "[Phase3:Finalize] Packed %d blocks, %d overflow warnings.",
        len(context_safe_pack),
        len(overflow_warnings),
    )
    return {
        "context_safe_pack": context_safe_pack,
        "overflow_warnings": overflow_warnings,
    }
