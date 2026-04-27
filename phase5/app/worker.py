"""
OmniLocal - Phase 5 Worker Logic: rebuild localized PDF text boxes only.
"""

import os
from pathlib import Path

import fitz  # PyMuPDF >= 1.27


PROJECT_ROOT = Path(__file__).resolve().parents[2]


WINDOWS_FONTS_DIR = Path(r"C:\Windows\Fonts")
LINUX_FONTS_DIR = Path("/usr/share/fonts/truetype")
FONTS_DIR = WINDOWS_FONTS_DIR if WINDOWS_FONTS_DIR.exists() else LINUX_FONTS_DIR

FONT_FAMILIES = {
    "times": {
        "regular": FONTS_DIR / "times.ttf",
        "bold": FONTS_DIR / "timesbd.ttf",
        "italic": FONTS_DIR / "timesi.ttf",
        "bolditalic": FONTS_DIR / "timesbi.ttf",
    },
    "arial": {
        "regular": FONTS_DIR / "arial.ttf",
        "bold": FONTS_DIR / "arialbd.ttf",
        "italic": FONTS_DIR / "ariali.ttf",
        "bolditalic": FONTS_DIR / "arialbi.ttf",
    },
    "calibri": {
        "regular": FONTS_DIR / "calibri.ttf",
        "bold": FONTS_DIR / "calibrib.ttf",
        "italic": FONTS_DIR / "calibrii.ttf",
        "bolditalic": FONTS_DIR / "calibriz.ttf",
    },
}

BASE14_FONTS = {
    "serif": {
        "regular": "tiro",
        "bold": "tibo",
        "italic": "tiit",
        "bolditalic": "tibi",
    },
    "sans": {
        "regular": "helv",
        "bold": "hebo",
        "italic": "heit",
        "bolditalic": "hebi",
    },
}

_font_cache: dict[tuple[str, int], fitz.Font] = {}


def hex_color_to_tuple(color_int: int) -> tuple[float, float, float]:
    return (
        ((color_int >> 16) & 0xFF) / 255.0,
        ((color_int >> 8) & 0xFF) / 255.0,
        (color_int & 0xFF) / 255.0,
    )


def sanitize_bbox(bbox_list: list) -> fitz.Rect:
    if not bbox_list or len(bbox_list) != 4:
        return fitz.Rect(0, 0, 100, 100)

    x0, y0, x1, y1 = bbox_list

    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0

    if x1 - x0 < 4:
        x1 = x0 + 4
    if y1 - y0 < 4:
        y1 = y0 + 4

    x0 = max(0, x0)
    y0 = max(0, y0)

    return fitz.Rect(x0, y0, x1, y1)


def _variant_from_flags(flags: int) -> str:
    bold = bool(flags & (1 << 4))
    italic = bool(flags & (1 << 1))
    if bold and italic:
        return "bolditalic"
    if bold:
        return "bold"
    if italic:
        return "italic"
    return "regular"


def _font_family_name(font_name: str) -> str:
    lowered = (font_name or "").lower()
    if "arial" in lowered or "helvetica" in lowered:
        return "arial"
    if "calibri" in lowered:
        return "calibri"
    return "times"


def get_font(block: dict) -> fitz.Font:
    font_name = block.get("font", "") or ""
    flags = int(block.get("flags", 0) or 0)
    cache_key = (font_name, flags)
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    variant = _variant_from_flags(flags)
    family_name = _font_family_name(font_name)
    family = FONT_FAMILIES.get(family_name, FONT_FAMILIES["times"])
    candidate = family.get(variant)

    try:
        if candidate and candidate.exists():
            font = fitz.Font(fontfile=str(candidate))
        else:
            base14_family = BASE14_FONTS["sans" if family_name in {"arial", "calibri"} else "serif"]
            font = fitz.Font(base14_family[variant])
    except Exception:
        font = fitz.Font("helv")

    _font_cache[cache_key] = font
    return font


def choose_alignment(block: dict) -> int:
    original = (block.get("original_content", "") or block.get("text", "")).strip()
    font_size = float(block.get("size", 12.0) or 12.0)
    if font_size >= 18 and original and "\n" not in original and len(original) <= 80:
        return fitz.TEXT_ALIGN_CENTER
    return fitz.TEXT_ALIGN_LEFT


def _text_overflows(
    bbox: fitz.Rect,
    text: str,
    font: fitz.Font,
    font_size: float,
    align: int,
) -> bool:
    if bbox.width <= 0 or bbox.height <= 0:
        return True

    writer = fitz.TextWriter(fitz.Rect(0, 0, 9999, 9999))
    try:
        overflow = writer.fill_textbox(
            bbox,
            text,
            fontsize=font_size,
            font=font,
            align=align,
        )
        return bool(overflow)
    except (ValueError, RuntimeError):
        # PyMuPDF may raise when the starting line cannot be placed in a
        # narrow or short rectangle. Treat that as overflow and let the
        # caller shrink or skip gracefully.
        return True


def fit_text_in_bbox(
    bbox: fitz.Rect,
    text: str,
    font: fitz.Font,
    initial_size: float,
    align: int,
    min_ratio: float = 0.55,
) -> float:
    if initial_size <= 0:
        initial_size = 12.0

    if not text.strip():
        return initial_size

    if not _text_overflows(bbox, text, font, initial_size, align):
        return initial_size

    min_size = max(4.0, initial_size * min_ratio)
    if _text_overflows(bbox, text, font, min_size, align):
        return max(4.0, min_size * 0.9)

    lo = min_size
    hi = initial_size
    best_fit = min_size

    for _ in range(14):
        mid = (lo + hi) / 2
        if _text_overflows(bbox, text, font, mid, align):
            hi = mid
        else:
            best_fit = mid
            lo = mid

    return best_fit


def collect_replacement_blocks(payload: dict) -> list[dict]:
    p3_output = payload.get("output_phase_3") or {}
    raw_blocks = p3_output.get("context_safe_localized_text_pack", []) or []

    replacements: list[dict] = []
    for block in raw_blocks:
        if block.get("source_type", "text") != "text":
            continue

        translated = (block.get("localized_content", "") or block.get("translated_content", "")).strip()
        original = (block.get("original_content", "") or block.get("text", "")).strip()
        if not translated or not original:
            continue

        if len(original) <= 1 and float(block.get("size", 0) or 0) > 40:
            continue

        clean_block = dict(block)
        clean_block["final_text"] = translated
        replacements.append(clean_block)

    return replacements


def group_by_page(blocks: list[dict]) -> dict[int, list[dict]]:
    pages: dict[int, list[dict]] = {}
    for block in blocks:
        page_id = int(block.get("page_id", 1) or 1)
        pages.setdefault(page_id, []).append(block)
    return pages


def rebuild_localized_pdf(payload: dict) -> dict:
    source_pdf_path = payload.get("source_pdf_path")
    print(f"\n[Phase 5] Starting localized text rebuild for: {source_pdf_path}", flush=True)
    if not source_pdf_path or not os.path.exists(source_pdf_path):
        raise ValueError(f"Source PDF not found: {source_pdf_path}")

    text_blocks = collect_replacement_blocks(payload)
    print(f"[Phase 5] Rebuilding {len(text_blocks)} text blocks from Phase 3", flush=True)

    doc = fitz.open(source_pdf_path)
    pages_map = group_by_page(text_blocks)
    stats = {"replaced": 0, "skipped": 0, "shrunk": 0, "pages_touched": 0}

    for page_id in sorted(pages_map.keys()):
        page_index = page_id - 1
        if page_index < 0 or page_index >= len(doc):
            stats["skipped"] += len(pages_map[page_id])
            continue

        page = doc[page_index]
        blocks = pages_map[page_id]
        if not blocks:
            continue

        stats["pages_touched"] += 1
        print(f"[Phase 5] Page {page_id}: rebuilding {len(blocks)} text boxes", flush=True)

        for block in blocks:
            bbox = sanitize_bbox(block.get("bbox", [0, 0, 0, 0]))
            page.add_redact_annot(bbox, fill=(1, 1, 1))
        page.apply_redactions()

        for block in blocks:
            bbox = sanitize_bbox(block.get("bbox", [0, 0, 0, 0]))
            translated = block.get("final_text", "")
            font_size = float(block.get("size", 12.0) or 12.0)
            color = hex_color_to_tuple(int(block.get("color", 0) or 0))
            align = choose_alignment(block)
            font = get_font(block)
            adjusted_size = fit_text_in_bbox(bbox, translated, font, font_size, align)

            if adjusted_size < font_size * 0.98:
                stats["shrunk"] += 1

            try:
                writer = fitz.TextWriter(page.rect)
                writer.fill_textbox(
                    bbox,
                    translated,
                    fontsize=adjusted_size,
                    font=font,
                    align=align,
                )
                writer.write_text(page, color=color)
                stats["replaced"] += 1
            except (ValueError, RuntimeError) as exc:
                stats["skipped"] += 1
                print(
                    f"[Phase 5 WARN] Skipped text on page {page_id} because bbox could not fit the first line: {exc}",
                    flush=True,
                )
            except Exception as exc:
                stats["skipped"] += 1
                print(f"[Phase 5 ERROR] Failed to draw text on page {page_id}: {exc}", flush=True)

    output_dir = PROJECT_ROOT / "uploads"
    output_dir.mkdir(exist_ok=True)
    output_filename = f"omnilocal_{Path(source_pdf_path).name}"
    output_path = output_dir / output_filename

    doc.save(str(output_path), garbage=4, deflate=True)
    doc.close()

    print(f"[Phase 5] Rebuild complete. Stats: {stats}", flush=True)
    print(f"[Phase 5] Output PDF saved to: {output_path}", flush=True)

    return {
        "output_pdf_path": str(output_path),
        "url": f"http://localhost:8005/output/{output_filename}",
        "stats": stats,
    }
