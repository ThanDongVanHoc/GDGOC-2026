# Phase 1 — Ingestion & Structural Parsing

> **Service Port:** `8001`  
> **Endpoint:** `POST /api/v1/phase1/run`  
> **Response:** `202 Accepted` (processes in background, fires webhook on completion)

---

## Overview

Phase 1 is the **entry point** of the OmniLocal pipeline. It takes a raw PDF and a project brief, then produces a **Standardized Pack** — a structured JSON containing every text block, image block, OCR-extracted text, and editability classification needed by downstream phases.

### Pipeline

```
PDF File ──┐
           ├──▶ PyMuPDF (text + image extraction)
           │         │
           │         ▼
           │    PaddleOCR (text in images)
           │         │
Brief ─────┤         ▼
           ├──▶ Gemini 2.5 Flash (metadata extraction)
           │         │
           │         ▼
           └──▶ Gemini 2.5 Flash (editability tagging)
                     │
                     ▼
              Standardized Pack (JSON)
```

### Optimizations Applied

| # | Technique | Where |
|---|-----------|-------|
| 1 | ⚡ `asyncio.gather` | All pages tagged concurrently by Gemini |
| 2 | 📦 Batching | All blocks on one page → single Gemini call |
| 3 | 🔧 `ProcessPoolExecutor` | PyMuPDF parsing + PaddleOCR inference |
| 4 | 💾 In-Memory | PDF as bytes stream, images as numpy arrays (zero disk I/O) |

---

## Input

### Orchestrator Payload (`POST /api/v1/phase1/run`)

```json
{
  "thread_id": "uuid-string",
  "source_pdf_path": "/absolute/path/to/book.pdf",
  "brief_path": "/absolute/path/to/brief.txt",
  "brief_text": "Optional raw text if brief_path is empty",
  "webhook_url": "http://orchestrator:8000/webhook"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `thread_id` | `string` | ✅ | Unique pipeline run ID |
| `source_pdf_path` | `string` | ✅ | Absolute path to the source PDF file |
| `brief_path` | `string` | ❌ | Path to project brief file (`.txt`, `.docx`) |
| `brief_text` | `string` | ❌ | Raw brief text (used if `brief_path` is empty) |
| `webhook_url` | `string` | ✅ | URL to POST results back to |

> **Note:** At least one of `brief_path` or `brief_text` should be provided. If neither is given, default GlobalMetadata constraints are used.

---

## Output

### Webhook Payload (sent to `webhook_url`)

```json
{
  "thread_id": "uuid-string",
  "result": {
    "global_metadata": { ... },
    "standardized_pack": [ ... ]
  },
  "error": null
}
```

---

### `global_metadata` — Global Constraints

Extracted from the project brief via Gemini 2.5 Flash.

```json
{
  "source_language": "EN",
  "target_language": "VI",
  "license_status": true,
  "author_attribution": "Written by Charles Perrault",
  "integrity_protection": true,
  "adaptation_rights": false,
  "translation_fidelity": "Strict",
  "plot_alteration": false,
  "cultural_localization": false,
  "preserve_main_names": true,
  "protected_names": ["Cinderella", "Prince Charming", "Fairy Godmother"],
  "no_retouching": true,
  "lock_character_color": true,
  "never_change_rules": ["Cinderella's glass slippers", "Fairy Godmother's sparkling wand"],
  "style_register": "children_under_10",
  "target_age_tone": 10,
  "glossary_strict_mode": true,
  "sfx_handling": "In_panel_subs",
  "satisfaction_clause": true,
  "allow_bg_edit": true,
  "max_drift_ratio": 0.2
}
```

| Field | Type | Description |
|-------|------|-------------|
| `source_language` | `str` | Source language code (e.g. `"EN"`) |
| `target_language` | `str` | Target language code (e.g. `"VI"`) |
| `license_status` | `bool` | Is the project legally licensed? |
| `author_attribution` | `str` | Required author credit format |
| `integrity_protection` | `bool` | Protect work integrity (Right of Integrity) |
| `adaptation_rights` | `bool` | Allow transcreation/adaptation |
| `translation_fidelity` | `str` | `"Strict"` or `"Explanatory"` |
| `plot_alteration` | `bool` | Can the plot be changed? |
| `cultural_localization` | `bool` | Can cultural elements be adapted? |
| `preserve_main_names` | `bool` | Keep character names untranslated |
| `protected_names` | `str[]` | Names that must NOT be translated |
| `no_retouching` | `bool` | Forbid image redrawing/retouching |
| `lock_character_color` | `bool` | Lock character colors |
| `never_change_rules` | `str[]` | Immutable visual traits |
| `style_register` | `str` | Target audience tone |
| `target_age_tone` | `int` | Target reader age |
| `glossary_strict_mode` | `bool` | Enforce glossary 100% |
| `sfx_handling` | `str` | `"In_panel_subs"`, `"Footnotes"`, or `"Keep"` |
| `satisfaction_clause` | `bool` | Licensor veto right |
| `allow_bg_edit` | `bool` | Allow background editing |
| `max_drift_ratio` | `float` | Max text-length drift ratio (0.0–1.0) |

---

### `standardized_pack` — Array of Page Layouts

Each element represents one PDF page:

```json
{
  "page_id": 1,
  "width": 595.0,
  "height": 842.0,
  "text_blocks": [
    {
      "content": "Once upon a time...",
      "bbox": [72.0, 100.0, 523.0, 130.0],
      "font": "Georgia",
      "size": 12.0,
      "color": 0,
      "flags": 0,
      "editability_tag": "editable"
    }
  ],
  "image_blocks": [
    {
      "bbox": [50.0, 200.0, 545.0, 600.0],
      "image_index": 0,
      "editability_tag": "semi-editable",
      "ocr_text_blocks": [
        {
          "content": "BOOM!",
          "bbox_in_image": [10.0, 20.0, 80.0, 45.0],
          "confidence": 0.95,
          "editability_tag": "editable"
        }
      ]
    }
  ]
}
```

#### Text Block Fields

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str` | Text content extracted by PyMuPDF |
| `bbox` | `float[4]` | Bounding box `[x0, y0, x1, y1]` in PDF points |
| `font` | `str` | Font family name |
| `size` | `float` | Font size in points |
| `color` | `int` | Text color as integer |
| `flags` | `int` | Font flags (bold, italic, etc.) |
| `editability_tag` | `str` | `"editable"` / `"semi-editable"` / `"non-editable"` |

#### Image Block Fields

| Field | Type | Description |
|-------|------|-------------|
| `bbox` | `float[4]` | Bounding box `[x0, y0, x1, y1]` in PDF points |
| `image_index` | `int` | Image index on the page |
| `editability_tag` | `str` | `"editable"` / `"semi-editable"` / `"non-editable"` |
| `ocr_text_blocks` | `array` | Text detected inside the image by PaddleOCR |

#### OCR Text Block Fields (nested inside Image Block)

| Field | Type | Description |
|-------|------|-------------|
| `content` | `str` | Text recognized by PaddleOCR |
| `bbox_in_image` | `float[4]` | Bounding box `[x0, y0, x1, y1]` **relative to the image** |
| `confidence` | `float` | OCR confidence score (0.0–1.0) |
| `editability_tag` | `str` | `"editable"` / `"semi-editable"` / `"non-editable"` |

#### Editability Tags

| Tag | Meaning | Example |
|-----|---------|---------|
| `editable` | Full permission to modify (text + image) | Story text, backgrounds |
| `semi-editable` | Only text can be changed, visuals preserved | Speech bubbles near characters |
| `non-editable` | Locked — must not be touched | Copyright, character faces, logos |

---

## Run Locally

```bash
cd phase1

# Install dependencies
pip install -r requirements.txt

# Start the service
uvicorn app.main:app --reload --port 8001

# Run end-to-end test (in another terminal)
python test_flow.py
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | API framework |
| `uvicorn` | ASGI server |
| `httpx` | Async HTTP client (webhook) |
| `pymupdf` | PDF parsing (`fitz`) |
| `pydantic` | Schema validation |
| `python-docx` | DOCX brief reading |
| `google-genai` | Gemini 2.5 Flash API |
| `python-dotenv` | Environment variable loading |
| `paddlepaddle` | PaddlePaddle framework |
| `paddleocr` | In-image text detection & recognition |
| `numpy` | Image array processing |
