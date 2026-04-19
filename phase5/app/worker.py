"""
OmniLocal — Phase 5 Worker Logic: PDF Rebuild.
"""

import fitz  # PyMuPDF >= 1.27
import os
from pathlib import Path

# Windows System Fonts (Times New Roman — full Vietnamese Unicode support)
FONTS_DIR = Path(r"C:\Windows\Fonts")
if not FONTS_DIR.exists():
    # Fallback for Linux (Azure)
    FONTS_DIR = Path("/usr/share/fonts/truetype")

# Attempt to find Times New Roman, fallback to Liberation Serif or generic
FONT_PATHS = {
    "regular": FONTS_DIR / "times.ttf",
    "bold": FONTS_DIR / "timesbd.ttf",
    "italic": FONTS_DIR / "timesi.ttf",
    "bolditalic": FONTS_DIR / "timesbi.ttf",
}

# Linux fallback if Windows fonts not found
if not FONT_PATHS["regular"].exists():
    # We will just depend on PyMuPDF's built in fallback for now if on Linux,
    # or the user can install msttcorefonts.
    pass

_font_cache = {}

def get_font(flags: int) -> fitz.Font:
    """Get cached fitz.Font object matching bold/italic flags."""
    bold = bool(flags & (1 << 4))
    italic = bool(flags & (1 << 1))
    key = (bold, italic)

    if key not in _font_cache:
        try:
            if bold and italic and FONT_PATHS["bolditalic"].exists():
                _font_cache[key] = fitz.Font(fontfile=str(FONT_PATHS["bolditalic"]))
            elif bold and FONT_PATHS["bold"].exists():
                _font_cache[key] = fitz.Font(fontfile=str(FONT_PATHS["bold"]))
            elif italic and FONT_PATHS["italic"].exists():
                _font_cache[key] = fitz.Font(fontfile=str(FONT_PATHS["italic"]))
            elif FONT_PATHS["regular"].exists():
                _font_cache[key] = fitz.Font(fontfile=str(FONT_PATHS["regular"]))
            else:
                # Base14 Fallback (limited Vietnamese)
                if bold and italic:
                    _font_cache[key] = fitz.Font("tibi")
                elif bold:
                    _font_cache[key] = fitz.Font("tibo")
                elif italic:
                    _font_cache[key] = fitz.Font("tiit")
                else:
                    _font_cache[key] = fitz.Font("tiro")
        except Exception:
            _font_cache[key] = fitz.Font("helv")

    return _font_cache[key]

def hex_color_to_tuple(color_int: int) -> tuple:
    r = ((color_int >> 16) & 0xFF) / 255.0
    g = ((color_int >> 8) & 0xFF) / 255.0
    b = (color_int & 0xFF) / 255.0
    return (r, g, b)

def fit_text_in_bbox(bbox: fitz.Rect, text: str, font: fitz.Font,
                     initial_size: float, min_ratio: float = 0.45) -> float:
    min_size = initial_size * min_ratio
    best_size = min_size
    
    tw = fitz.TextWriter(fitz.Rect(0, 0, 9999, 9999))
    if not tw.fill_textbox(bbox, text, fontsize=initial_size, font=font):
        return initial_size

    lo, hi = min_size, initial_size
    for _ in range(10):
        mid = (lo + hi) / 2
        tw = fitz.TextWriter(fitz.Rect(0, 0, 9999, 9999))
        if tw.fill_textbox(bbox, text, fontsize=mid, font=font):
            hi = mid
        else:
            best_size = mid
            lo = mid
    return best_size

def rebuild_localized_pdf(payload: dict) -> dict:
    source_pdf_path = payload.get("source_pdf_path")
    print(f"\n[Phase 5] Starting PDF Rebuild for: {source_pdf_path}", flush=True)
    if not source_pdf_path or not os.path.exists(source_pdf_path):
        print(f"[Phase 5 ERROR] Source PDF not found: {source_pdf_path}", flush=True)
        raise ValueError(f"Source PDF not found: {source_pdf_path}")

    # Phase 3 sends 'context_safe_localized_text_pack' (fully culturally adapted)
    # If not present for some reason, fallback to Phase 2 'verified_text_pack'
    p3_output = payload.get("output_phase_3") or {}
    text_blocks = p3_output.get("context_safe_localized_text_pack", [])
    if not text_blocks:
        print("[Phase 5] No Phase 3 context pack found, falling back to Phase 2 data...", flush=True)
        p2_output = payload.get("output_phase_2") or {}
        # Phase 2 format could be a flat list or nested dict
        p2_pack = p2_output.get("verified_text_pack", [])
        if isinstance(p2_pack, dict) and "pages" in p2_pack:
            text_blocks = []
            for p in p2_pack["pages"]:
                text_blocks.extend(p.get("text_blocks", []))
        elif isinstance(p2_pack, list):
            text_blocks = p2_pack

    print(f"[Phase 5] Loaded {len(text_blocks)} candidate blocks for replacement", flush=True)

    pages_map = {}
    for block in text_blocks:
        # Add robust parsing for content
        translated = block.get("localized_content", "")
        if not translated:
            translated = block.get("translated_content", "")
        
        original = block.get("original_content", "")
        if not original:
            original = block.get("text", "")

        block["final_text"] = translated # Ensure it's set
        pid = block.get("page_id", 1)
        pages_map.setdefault(pid, []).append(block)

    # ── Phase 4 Image Parsing ──
    output_phase_4 = payload.get("output_phase_4", {})
    image_results = output_phase_4.get("results", []) if isinstance(output_phase_4, dict) else []
    
    image_pages_map = {}
    for img_data in image_results:
        if img_data.get("status") == "success" and img_data.get("image"):
            pid = img_data.get("page_id", 1)
            image_pages_map.setdefault(pid, []).append(img_data)

    doc = fitz.open(source_pdf_path)
    stats = {"replaced": 0, "skipped": 0, "shrunk": 0, "replaced_images": 0, "skipped_images": 0}

    all_pages = set(pages_map.keys()).union(set(image_pages_map.keys()))

    for page_id in sorted(all_pages):
        blocks = pages_map.get(page_id, [])
        img_blocks = image_pages_map.get(page_id, [])
        
        page_idx = page_id - 1
        if page_idx < 0 or page_idx >= len(doc):
            continue

        page = doc[page_idx]

        replace_list = []
        for block in blocks:
            # Add robust parsing for content
            translated = block.get("final_text", "")
            original = block.get("original_content", "")
            if not original:
                original = block.get("text", "")

            if not translated or not original:
                stats["skipped"] += 1
                continue
            
            if len(original) <= 1 and block.get("size", 0) > 40:
                stats["skipped"] += 1
                continue
            
            replace_list.append(block)

        if not replace_list and not img_blocks:
            print(f"[Phase 5] Page {page_id}: Skipped all blocks (No text or image changes detected)")
            continue
            
        if replace_list:
            print(f"[Phase 5] Page {page_id}: Replacing {len(replace_list)} text blocks...")

        for block in replace_list:
            bbox = fitz.Rect(block.get("bbox", [0, 0, 0, 0]))
            page.add_redact_annot(bbox, fill=(1, 1, 1))
        page.apply_redactions()

        for block in replace_list:
            bbox = fitz.Rect(block.get("bbox", [0, 0, 0, 0]))
            translated = block.get("final_text", "")
            font_size = block.get("size", 12.0)
            color_int = block.get("color", 0)
            flags = block.get("flags", 0)

            if bbox.width < 1 or bbox.height < 1:
                stats["skipped"] += 1
                continue

            color = hex_color_to_tuple(color_int)
            font = get_font(flags)
            align = fitz.TEXT_ALIGN_CENTER if font_size > 18 else fitz.TEXT_ALIGN_LEFT
            adjusted_size = fit_text_in_bbox(bbox, translated, font, font_size)

            if adjusted_size < font_size * 0.95:
                stats["shrunk"] += 1

            try:
                tw = fitz.TextWriter(page.rect)
                tw.fill_textbox(bbox, translated, fontsize=adjusted_size, font=font, align=align)
                tw.write_text(page, color=color)
                stats["replaced"] += 1
            except Exception as e:
                print(f"[Phase 5 ERROR] Failed to draw text on pg {page_id}: {e}")

        # ── Image Insertion Logic ──
        if img_blocks:
            print(f"[Phase 5] Page {page_id}: Inserting {len(img_blocks)} images...")
            import base64
            for img_data in img_blocks:
                bbox_list = img_data.get("bbox", [0, 0, 0, 0])
                b64_str = img_data.get("image")
                try:
                    rect = fitz.Rect(bbox_list)
                    img_bytes = base64.b64decode(b64_str)
                    page.insert_image(rect, stream=img_bytes)
                    stats["replaced_images"] += 1
                except Exception as e:
                    stats["skipped_images"] += 1
                    print(f"[Phase 5 ERROR] Failed to insert image on pg {page_id}: {e}")

    # Save output
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    out_filename = f"omnilocal_{Path(source_pdf_path).name}"
    out_path = output_dir / out_filename
    
    doc.save(str(out_path), garbage=4, deflate=True)
    doc.close()

    print(f"\n[Phase 5] Rebuild Complete! stats: {stats}")
    print(f"[Phase 5] Output PDF saved to: {out_path}")

    return {
        "output_pdf_path": str(out_path),
        "url": f"http://localhost:8005/output/{out_filename}",
        "stats": stats
    }
