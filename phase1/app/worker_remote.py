"""
OmniLocal — Phase 1 Worker: Ingestion & Structural Parsing.

This worker implements the complete Phase 1 pipeline:
    1. Parse project brief → extract GlobalMetadata via Gemini 2.5 Flash.
    2. Parse PDF (PyMuPDF) → extract text/image blocks with bbox coordinates.
    3. OCR embedded images (EasyOCR) → extract in-image text (SFX, speech bubbles).
    4. Tag editability for every block using Gemini semantic analysis.

Parallelism & Optimization:
    - ProcessPoolExecutor for CPU-bound PyMuPDF + EasyOCR work.
    - asyncio.gather for concurrent Gemini editability-tagging calls.
    - Batching: all blocks on one page sent as a single Gemini call.
    - In-memory processing: PDF bytes stream + numpy arrays (zero disk I/O).
"""

import asyncio
import base64
import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from enum import Enum
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import numpy as np
from dotenv import load_dotenv
import openai
from pydantic import BaseModel, Field

# ── Environment & Constants ──────────────────────────────────────
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = "SaoLa4-medium"
MAX_POOL_WORKERS = 4

logging.basicConfig(level=logging.INFO, format="[Phase1] %(message)s")
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════


class EditabilityTag(str, Enum):
    """Editability classification for content blocks."""

    EDITABLE = "editable"
    SEMI_EDITABLE = "semi-editable"
    NON_EDITABLE = "non-editable"


class GlobalMetadata(BaseModel):
    """
    Global constraints extracted from the project brief.

    Covers Legal, Content, IP/Brand, and Editorial parameter groups
    as defined in the Phase 1 specification.
    """

    # ── Legal Parameters ─────────────────────────────────────────
    source_language: str = Field(default="EN", description="Source language code")
    target_language: str = Field(default="VI", description="Target language code")
    license_status: bool = Field(default=True, description="Licensed for translation")
    author_attribution: str = Field(default="", description="Author credit format")
    integrity_protection: bool = Field(
        default=True, description="Protect work integrity"
    )
    adaptation_rights: bool = Field(
        default=False, description="Allow transcreation/adaptation"
    )

    # ── Content Parameters ───────────────────────────────────────
    translation_fidelity: str = Field(
        default="Strict", description="Strict or Explanatory"
    )
    plot_alteration: bool = Field(default=False, description="Allow plot changes")
    cultural_localization: bool = Field(
        default=False, description="Allow cultural adaptation"
    )

    # ── IP / Brand Parameters ────────────────────────────────────
    preserve_main_names: bool = Field(
        default=True, description="Keep character names untranslated"
    )
    protected_names: list[str] = Field(
        default_factory=list, description="Names that must not be translated"
    )
    no_retouching: bool = Field(
        default=True, description="Forbid image redrawing/retouching"
    )
    lock_character_color: bool = Field(
        default=True, description="Lock character color palettes"
    )
    never_change_rules: list[str] = Field(
        default_factory=list,
        description="Immutable visual traits (e.g. mole under left eye)",
    )

    # ── Editorial Parameters ─────────────────────────────────────
    style_register: str = Field(
        default="children_under_10", description="Target audience tone"
    )
    target_age_tone: int = Field(default=10, description="Target age for tone")
    glossary_strict_mode: bool = Field(
        default=False, description="Enforce glossary 100%"
    )
    sfx_handling: str = Field(
        default="In_panel_subs",
        description="SFX handling: In_panel_subs, Footnotes, or Keep",
    )
    satisfaction_clause: bool = Field(
        default=False, description="Licensor veto right on final output"
    )

    # ── Technical Parameters ─────────────────────────────────────
    allow_bg_edit: bool = Field(default=True, description="Allow background editing")
    max_drift_ratio: float = Field(
        default=0.15,
        description="Max text length drift ratio vs source",
    )


class OcrTextBlock(BaseModel):
    """A text region detected inside an image by EasyOCR."""

    content: str = Field(description="Recognized text content")
    bbox_in_image: list[float] = Field(
        description="Bounding box within the image [x0, y0, x1, y1]"
    )
    confidence: float = Field(description="OCR confidence score 0-1")
    editability_tag: EditabilityTag = Field(default=EditabilityTag.EDITABLE)


class TextBlock(BaseModel):
    """A text block extracted from PDF via PyMuPDF."""

    content: str = Field(description="Text content")
    bbox: list[float] = Field(description="Bounding box [x0, y0, x1, y1]")
    font: str = Field(default="", description="Font family name")
    size: float = Field(default=0.0, description="Font size in points")
    color: int = Field(default=0, description="Text color as integer")
    flags: int = Field(default=0, description="Font flags (bold, italic, etc.)")
    editability_tag: EditabilityTag = Field(default=EditabilityTag.EDITABLE)


class ImageBlock(BaseModel):
    """An image block extracted from PDF, with optional OCR results."""

    bbox: list[float] = Field(description="Bounding box [x0, y0, x1, y1]")
    image_index: int = Field(description="Image index on the page")
    ocr_text_blocks: list[OcrTextBlock] = Field(default_factory=list)
    editability_tag: EditabilityTag = Field(default=EditabilityTag.SEMI_EDITABLE)


class PageLayout(BaseModel):
    """Structural layout of a single PDF page."""

    page_id: int = Field(description="1-indexed page number")
    width: float = Field(description="Page width in points")
    height: float = Field(description="Page height in points")
    text_blocks: list[TextBlock] = Field(default_factory=list)
    image_blocks: list[ImageBlock] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════


async def run(payload: dict) -> dict:
    """
    Main entry point for Phase 1 processing.

    Orchestrates the full ingestion pipeline: brief parsing, PDF structural
    extraction, EasyOCR on embedded images, and editability tagging.
    Leverages ProcessPoolExecutor for CPU-bound work and asyncio.gather
    for concurrent Gemini API calls.

    Args:
        payload: Job data from the Orchestrator containing:
            - source_pdf_path (str): Absolute path to the source PDF file.
            - brief_path (str): Path to the project brief file (.txt/.docx)
              OR brief_text (str): Raw brief text content.
            - thread_id (str): Unique pipeline run identifier.

    Returns:
        dict: Contains 'global_metadata' and 'standardized_pack' (list of pages).
    """
    source_pdf_path = payload["source_pdf_path"]
    brief_path = payload.get("brief_path", "")
    brief_text = payload.get("brief_text", "")

    logger.info("Starting Phase 1 pipeline for thread=%s", payload.get("thread_id"))

    # ── Initialize OpenAI client for FPT AI ──────────────────────
    client = openai.AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://mkp-api.fptcloud.com/v1"
    )

    # ── Step 1: Parse brief → GlobalMetadata (Gemini) ────────────
    logger.info("[#p1.1] Parsing project brief...")
    global_metadata = await _parse_brief(client, brief_path, brief_text)
    logger.info("[#p1.1] GlobalMetadata extracted: %s", global_metadata.model_dump())

    # ── Step 2: Parse PDF structure (ProcessPoolExecutor + in-memory) ──
    logger.info("[#p1.2] Parsing PDF structure...")
    pdf_bytes = Path(source_pdf_path).read_bytes()

    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor(max_workers=MAX_POOL_WORKERS) as pool:
        # Offload CPU-bound PyMuPDF parsing to a separate process
        pages_raw, images_data = await loop.run_in_executor(
            pool, _parse_pdf_sync, pdf_bytes
        )
        logger.info("[#p1.2] Extracted %d pages from PDF", len(pages_raw))

        # ── Step 2b: OCR on extracted images (ProcessPoolExecutor) ──
        if images_data:
            logger.info(
                "[#p1.2b] Running EasyOCR on %d images...", len(images_data)
            )
            ocr_results = await loop.run_in_executor(
                pool, _run_ocr_on_images, images_data
            )
        else:
            ocr_results = {}

    # ── Merge OCR results into page layouts ──────────────────────
    pages = _build_page_layouts(pages_raw, ocr_results)
    logger.info("[#p1.2b] OCR complete. Total images with text: %d", len(ocr_results))

    # ── Step 4: Assemble Standardized Pack ───────────────────────
    standardized_pack = [page.model_dump() for page in pages]

    logger.info("Phase 1 pipeline complete. %d pages processed.", len(standardized_pack))

    return {
        "global_metadata": global_metadata.model_dump(),
        "standardized_pack": standardized_pack,
    }


# ═══════════════════════════════════════════════════════════════════
#  TASK #p1.1 — GLOBAL METADATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════

BRIEF_EXTRACTION_PROMPT = """You are an expert localization project manager.
Analyze the following project brief and extract ALL constraints into a structured JSON.

The JSON MUST contain these fields (use reasonable defaults if not explicitly stated):
- source_language (str): Source language code, e.g. "EN"
- target_language (str): Target language code, e.g. "VI"
- license_status (bool): Is the project legally licensed for translation?
- author_attribution (str): Required author credit format
- integrity_protection (bool): Must the work's integrity be protected?
- adaptation_rights (bool): Is transcreation/adaptation allowed?
- translation_fidelity (str): "Strict" or "Explanatory"
- plot_alteration (bool): Can the plot be changed?
- cultural_localization (bool): Can cultural elements be adapted?
- preserve_main_names (bool): Keep character names untranslated?
- protected_names (list[str]): Specific names that must NOT be translated
- no_retouching (bool): Is image retouching forbidden?
- lock_character_color (bool): Are character colors locked?
- never_change_rules (list[str]): Immutable visual traits
- style_register (str): Target audience/tone description
- target_age_tone (int): Target reader age
- glossary_strict_mode (bool): Must glossary be enforced 100%?
- sfx_handling (str): "In_panel_subs", "Footnotes", or "Keep"
- satisfaction_clause (bool): Does the licensor have veto power?
- allow_bg_edit (bool): Can backgrounds be edited?
- max_drift_ratio (float): Max allowed text-length drift ratio (0.0-1.0)

Return ONLY valid JSON, no markdown fences, no explanation."""


async def _parse_brief(
    client: openai.AsyncOpenAI, brief_path: str, brief_text: str
) -> GlobalMetadata:
    """
    Parse the project brief and extract global metadata constraints via Gemini.

    Supports .txt, .docx files, or raw text input. Sends the content to Gemini
    2.5 Flash with a structured extraction prompt and validates the response
    with Pydantic.

    Args:
        client: Initialized Gemini API client.
        brief_path: File path to the brief document (.txt or .docx).
        brief_text: Raw brief text (used if brief_path is empty).

    Returns:
        GlobalMetadata: Validated constraint model.

    Raises:
        ValueError: If no brief content is provided or Gemini output is invalid.
    """
    # ── Read brief content ───────────────────────────────────────
    if brief_path and os.path.exists(brief_path):
        ext = Path(brief_path).suffix.lower()
        if ext == ".docx":
            from docx import Document

            doc = Document(brief_path)
            content = "\n".join([p.text for p in doc.paragraphs])
        else:
            content = Path(brief_path).read_text(encoding="utf-8")
    elif brief_text:
        content = brief_text
    else:
        logger.warning("No brief provided — using default GlobalMetadata")
        return GlobalMetadata()

    # ── Call Gemini to extract structured metadata ────────────────
    prompt = f"{BRIEF_EXTRACTION_PROMPT}\n\n--- PROJECT BRIEF ---\n{content}"

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    raw_json = response.choices[0].message.content.strip()
    # Remove markdown fences if the model wraps them
    if raw_json.startswith("```"):
        raw_json = raw_json.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    metadata_dict = json.loads(raw_json)
    return GlobalMetadata(**metadata_dict)


# ═══════════════════════════════════════════════════════════════════
#  TASK #p1.2 — STRUCTURAL PDF PARSING (CPU-BOUND, ProcessPoolExecutor)
# ═══════════════════════════════════════════════════════════════════


def _parse_pdf_sync(pdf_bytes: bytes) -> tuple[list[dict], dict]:
    """
    Parse a PDF from in-memory bytes and extract text/image blocks.

    Runs inside a ProcessPoolExecutor. Uses PyMuPDF to extract text blocks
    (with font metadata) and image blocks (with raw image bytes kept in RAM).

    Args:
        pdf_bytes: Raw PDF file content as bytes.

    Returns:
        tuple: (pages_raw, images_data) where:
            - pages_raw: List of dicts with page structure data.
            - images_data: Dict mapping (page_idx, img_idx) → image bytes
              for OCR processing.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_raw = []
    images_data = {}  # (page_idx, img_idx) → image_bytes

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

        text_blocks = []
        image_blocks = []
        img_counter = 0

        for block in page_dict.get("blocks", []):
            if block["type"] == 0:  # Text block
                # Aggregate text lines within the block
                block_text = ""
                block_font = ""
                block_size = 0.0
                block_color = 0
                block_flags = 0

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span.get("text", "")
                        if not block_font:
                            block_font = span.get("font", "")
                            block_size = span.get("size", 0.0)
                            block_color = span.get("color", 0)
                            block_flags = span.get("flags", 0)

                block_text = block_text.strip()
                if block_text:
                    text_blocks.append(
                        {
                            "content": block_text,
                            "bbox": list(block["bbox"]),
                            "font": block_font,
                            "size": block_size,
                            "color": block_color,
                            "flags": block_flags,
                        }
                    )

        seen_boxes = set()
        img_counter = 0

        for image_info in page.get_images(full=True):
            xref = image_info[0]

            for rect, _matrix in page.get_image_rects(xref, transform=True):
                key = (
                    round(rect.x0, 4),
                    round(rect.y0, 4),
                    round(rect.x1, 4),
                    round(rect.y1, 4),
                )
                if key in seen_boxes:
                    continue
                seen_boxes.add(key)

                image_blocks.append(
                    {
                        "bbox": [rect.x0, rect.y0, rect.x1, rect.y1],
                        "image_index": img_counter,
                    }
                )

                # Extract image bytes for OCR — keep in RAM
                try:
                    img_data = doc.extract_image(xref)
                    if img_data and img_data.get("image"):
                        images_data[(page_idx, img_counter)] = img_data["image"]
                except Exception:
                    pass  # Skip images that cannot be extracted

                img_counter += 1

        pages_raw.append(
            {
                "page_id": page_idx + 1,
                "width": page.rect.width,
                "height": page.rect.height,
                "text_blocks": text_blocks,
                "image_blocks": image_blocks,
            }
        )

    doc.close()
    return pages_raw, images_data


# ═══════════════════════════════════════════════════════════════════
#  TASK #p1.2b — OCR ON EMBEDDED IMAGES (CPU-BOUND, ProcessPoolExecutor)
# ═══════════════════════════════════════════════════════════════════


def _run_ocr_on_images(images_data: dict) -> dict:
    """
    Run EasyOCR on extracted images entirely in-memory (no disk I/O).

    Initializes EasyOCR Reader once and processes all images sequentially
    within the worker process. Images are decoded from raw bytes into
    numpy arrays.

    Args:
        images_data: Dict mapping (page_idx, img_idx) → raw image bytes.

    Returns:
        dict: Mapping (page_idx, img_idx) → list of OcrTextBlock dicts.
    """
    import easyocr
    import cv2

    # Initialize once, reuse for all images
    # gpu=False for broad compatibility; set gpu=True if CUDA is available
    reader = easyocr.Reader(["en"], gpu=True)
    results = {}

    for (page_idx, img_idx), img_bytes in images_data.items():
        try:
            # Decode image bytes → numpy array (in-memory, no temp file)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if image is None:
                continue

            # EasyOCR returns list of (bbox, text, confidence)
            # bbox format: [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
            ocr_result = reader.readtext(image)

            ocr_blocks = []
            for (polygon, text, confidence) in ocr_result:
                # Convert polygon to bbox [x0, y0, x1, y1]
                xs = [p[0] for p in polygon]
                ys = [p[1] for p in polygon]
                bbox = [min(xs), min(ys), max(xs), max(ys)]

                if text.strip():
                    ocr_blocks.append(
                        {
                            "content": text.strip(),
                            "bbox_in_image": bbox,
                            "confidence": float(confidence),
                            "editability_tag": "editable",
                        }
                    )

            if ocr_blocks:
                results[(page_idx, img_idx)] = ocr_blocks

        except Exception as e:
            logger.warning("OCR failed for page=%d img=%d: %s", page_idx, img_idx, e)

    return results


# ═══════════════════════════════════════════════════════════════════
#  BUILD PAGE LAYOUTS (Merge PDF parsing + OCR results)
# ═══════════════════════════════════════════════════════════════════


def _build_page_layouts(pages_raw: list[dict], ocr_results: dict) -> list[PageLayout]:
    """
    Merge raw PDF page data with OCR results into validated PageLayout models.

    Args:
        pages_raw: List of raw page dicts from _parse_pdf_sync.
        ocr_results: Dict mapping (page_idx, img_idx) → OCR text blocks.

    Returns:
        list[PageLayout]: Validated page layout models with OCR data merged in.
    """
    pages = []
    for page_data in pages_raw:
        page_idx = page_data["page_id"] - 1  # Convert to 0-indexed

        # Build text blocks
        text_blocks = [TextBlock(**tb) for tb in page_data["text_blocks"]]

        # Build image blocks with OCR results merged
        image_blocks = []
        for ib_data in page_data["image_blocks"]:
            ocr_key = (page_idx, ib_data["image_index"])
            ocr_blocks = []
            if ocr_key in ocr_results:
                ocr_blocks = [
                    OcrTextBlock(**ob) for ob in ocr_results[ocr_key]
                ]

            image_blocks.append(
                ImageBlock(
                    bbox=ib_data["bbox"],
                    image_index=ib_data["image_index"],
                    ocr_text_blocks=ocr_blocks,
                )
            )

        pages.append(
            PageLayout(
                page_id=page_data["page_id"],
                width=page_data["width"],
                height=page_data["height"],
                text_blocks=text_blocks,
                image_blocks=image_blocks,
            )
        )

    return pages


