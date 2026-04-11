"""Post-processor: MinerU raw output → #p1.2 PageLayout models.

MinerU writes a ``content_list.json`` alongside the Markdown file.
Each entry in the content list has a ``type`` field (``text``, ``image``,
``table``, ``equation``, etc.) plus bounding-box coordinates.

This module groups those entries by page and maps them into the
:class:`~models.PageLayout` Pydantic models expected by the rest of
the OmniLocal pipeline.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .models import DocumentPack, ImageBlock, PageLayout, TextBlock

logger = logging.getLogger(__name__)

# MinerU content-list entry types that count as *text*
_TEXT_TYPES: frozenset[str] = frozenset({
    "text",
    "title",
    "interline_equation",
    "table",          # tables are exported as HTML text
    "table_caption",
    "table_footnote",
    "footnote",
})

# Types treated as *image* regions
_IMAGE_TYPES: frozenset[str] = frozenset({
    "image",
    "image_body",
    "image_caption",
    "figure",
})


def _safe_bbox(raw: Any) -> list[float] | None:
    """Attempt to normalise a bbox value from various MinerU formats.

    Args:
        raw: The raw bbox data — usually ``[x0, y0, x1, y1]`` but may
             sometimes arrive as nested list or ``None``.

    Returns:
        A flat ``[x0, y0, x1, y1]`` list of floats, or ``None`` if the
        input is unusable.
    """
    if raw is None:
        return None
    if isinstance(raw, dict):
        # Some versions use {"x0": ..., "y0": ..., "x1": ..., "y1": ...}
        try:
            return [float(raw["x0"]), float(raw["y0"]),
                    float(raw["x1"]), float(raw["y1"])]
        except (KeyError, TypeError, ValueError):
            return None
    try:
        flat = [float(v) for v in raw]
        if len(flat) == 4:
            return flat
    except (TypeError, ValueError):
        pass
    return None


# ------------------------------------------------------------------
# Public helpers
# ------------------------------------------------------------------

def load_content_list(content_list_path: Path) -> list[dict[str, Any]]:
    """Load and return the MinerU ``content_list.json`` file.

    Args:
        content_list_path: Absolute or relative ``Path`` to the JSON file.

    Returns:
        The deserialised list of content entries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(content_list_path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return data
    # Some versions wrap in {"content_list": [...]}
    if isinstance(data, dict) and "content_list" in data:
        return data["content_list"]
    logger.warning(
        "Unexpected content_list.json structure — returning as-is."
    )
    return data if isinstance(data, list) else []


def build_page_layouts(
    content_list: list[dict[str, Any]],
    page_dimensions: dict[int, tuple[float, float]] | None = None,
) -> list[PageLayout]:
    """Convert a MinerU content list into per-page ``PageLayout`` objects.

    Args:
        content_list: Raw entries from ``content_list.json``.
        page_dimensions: Optional mapping of ``page_id → (width, height)``
            obtained from the PDF metadata.  If ``None``, default A4
            dimensions (595 × 842 pt) are assumed.

    Returns:
        Ordered list of :class:`PageLayout` instances, one per page.
    """
    # Defaults for A4 in PDF points
    default_width: float = 595.0
    default_height: float = 842.0

    # Accumulate blocks per page
    text_by_page: dict[int, list[TextBlock]] = {}
    image_by_page: dict[int, list[ImageBlock]] = {}
    seen_pages: set[int] = set()

    for entry in content_list:
        # Determine page_id — MinerU uses 0-indexed internally for some
        # versions, but #p1.2 expects 1-indexed.
        raw_page = entry.get("page_idx", entry.get("page_id", 0))
        page_id = int(raw_page) + 1  # convert 0-index → 1-index
        seen_pages.add(page_id)

        entry_type = str(entry.get("type", "text")).lower()
        bbox = _safe_bbox(entry.get("bbox"))

        if entry_type in _TEXT_TYPES:
            content = entry.get("text", entry.get("content", ""))
            if not content and entry_type == "table":
                # Tables may be stored as HTML under 'html'
                content = entry.get("html", "")
            if bbox is None:
                logger.debug(
                    "Skipping text entry without bbox on page %d", page_id
                )
                continue
            text_by_page.setdefault(page_id, []).append(
                TextBlock(content=str(content), bbox=bbox)
            )

        elif entry_type in _IMAGE_TYPES:
            if bbox is None:
                logger.debug(
                    "Skipping image entry without bbox on page %d", page_id
                )
                continue
            img_path = entry.get("img_path", entry.get("image_path"))
            image_by_page.setdefault(page_id, []).append(
                ImageBlock(
                    bbox=bbox,
                    image_path=str(img_path) if img_path else None,
                )
            )

        else:
            # Unknown type — try to include as text if content exists
            content = entry.get("text", entry.get("content", ""))
            if content and bbox is not None:
                text_by_page.setdefault(page_id, []).append(
                    TextBlock(content=str(content), bbox=bbox)
                )

    # Build ordered page list
    pages: list[PageLayout] = []
    for pid in sorted(seen_pages):
        w, h = (default_width, default_height)
        if page_dimensions and pid in page_dimensions:
            w, h = page_dimensions[pid]
        pages.append(
            PageLayout(
                page_id=pid,
                width=w,
                height=h,
                text_blocks=text_by_page.get(pid, []),
                image_blocks=image_by_page.get(pid, []),
            )
        )

    return pages


def build_document_pack(
    content_list_path: Path,
    source_file: str,
    markdown_content: str | None = None,
    page_dimensions: dict[int, tuple[float, float]] | None = None,
) -> DocumentPack:
    """One-shot helper: load content list → build full DocumentPack.

    Args:
        content_list_path: Path to ``content_list.json``.
        source_file: Original PDF filename (for metadata).
        markdown_content: Optional Markdown string to embed.
        page_dimensions: Optional page-size mapping.

    Returns:
        A fully populated :class:`DocumentPack`.
    """
    entries = load_content_list(content_list_path)
    pages = build_page_layouts(entries, page_dimensions)
    return DocumentPack(
        source_file=source_file,
        total_pages=len(pages),
        pages=pages,
        markdown_content=markdown_content,
    )
