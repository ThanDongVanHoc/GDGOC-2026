# Phase 2 — Constrained Translation & Feedback Loop

> **Service Port:** `8002`  
> **Endpoint:** `POST /api/v1/phase2/run`  
> **Response:** `202 Accepted` (processes in background, fires webhook on completion)

---

## Overview

Phase 2 receives the **Standardized Pack** from Phase 1 and translates all editable text (both PDF text blocks and OCR-extracted in-image text) from the source language to the target language. Translation is constrained by `global_metadata` rules and quality-controlled through an **AI Translator ↔ Reviser feedback loop** with a circuit breaker.

### Pipeline

```
Standardized Pack (Phase 1) ──▶ Semantic Chunking (15 pages/chunk)
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Translator Agent │◀──── feedback (reason)
                              │  (Gemini 2.5 FL) │         │
                              └────────┬────────┘         │
                                       │ draft             │
                                       ▼                   │
                              ┌─────────────────┐         │
                              │  Reviser Agent   │         │
                              │  (Gemini 2.5 FL) │         │
                              └────────┬────────┘         │
                                       │                   │
                                score ≥ 8? ── NO ── retry < 3?
                                       │                   │
                                      YES                  NO
                                       │                   │
                                       ▼                   ▼
                                ✅ Verified          ⚠️ Circuit Break
                                                    (keep + WARNING)
                                       │                   │
                                       └───────┬───────────┘
                                               ▼
                                     Verified Text Pack (JSON)
```

### Optimizations Applied

| # | Technique | Where |
|---|-----------|-------|
| 1 | ⚡ `asyncio.gather` | All chunks translated concurrently |
| 2 | 📦 Batching | 15 pages of text blocks → single Gemini call per chunk |
| 3 | 💾 In-Memory | Entire pipeline operates on JSON dicts (zero disk I/O) |
| 4 | 🔄 Context Caching | `global_metadata` system prompt cached once via Gemini API, reused for ALL translator + reviser calls |

---

## Input

### Orchestrator Payload (`POST /api/v1/phase2/run`)

```json
{
  "thread_id": "uuid-string",
  "standardized_pack": [ ... ],
  "global_metadata": { ... },
  "webhook_url": "http://orchestrator:8000/webhook"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `thread_id` | `string` | ✅ | Unique pipeline run ID |
| `standardized_pack` | `array` | ✅ | Page layouts from Phase 1 (see [Phase 1 output](../phase1/README.md#standardized_pack--array-of-page-layouts)) |
| `global_metadata` | `object` | ✅ | Global constraints from Phase 1 (see [Phase 1 output](../phase1/README.md#global_metadata--global-constraints)) |
| `webhook_url` | `string` | ✅ | URL to POST results back to |

> **Note:** Only blocks tagged `editable` or `semi-editable` are sent for translation. Blocks tagged `non-editable` are skipped entirely.

---

## Output

### Webhook Payload (sent to `webhook_url`)

```json
{
  "thread_id": "uuid-string",
  "result": {
    "verified_text_pack": [ ... ],
    "translation_warnings": [ ... ]
  },
  "error": null
}
```

---

### `verified_text_pack` — Array of Translated Blocks

Each element represents one translated text block:

```json
{
  "original_content": "Once upon a time, there lived a brave little girl named Cinderella.",
  "translated_content": "Ngày xửa ngày xưa, có một cô bé dũng cảm tên là Cinderella.",
  "bbox": [72.0, 100.0, 523.0, 130.0],
  "page_id": 2,
  "source_type": "text",
  "font": "Georgia",
  "size": 12.0,
  "color": 0,
  "flags": 0,
  "warning": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `original_content` | `str` | Source text (unchanged) |
| `translated_content` | `str` | Vietnamese translation |
| `bbox` | `float[4]` | Original bounding box `[x0, y0, x1, y1]` from Phase 1 |
| `page_id` | `int` | Source page number |
| `source_type` | `str` | **`"text"`** = PDF text layer, **`"ocr"`** = text inside an image |
| `font` | `str` | Original font family (for Phase 4 compositing) |
| `size` | `float` | Original font size in points |
| `color` | `int` | Original text color |
| `flags` | `int` | Original font flags (bold, italic, etc.) |
| `warning` | `str\|null` | Warning message if translation did not pass review, otherwise `null` |

#### `source_type` — Critical for Phase 4

| Value | Meaning | Phase 4 Action |
|-------|---------|----------------|
| `"text"` | Text from PDF text layer (PyMuPDF) | Replace text in PDF directly |
| `"ocr"` | Text detected inside an image (PaddleOCR) | Requires image inpainting + text overlay |

---

### `translation_warnings` — Array of Warning Objects

Only present for chunks that failed the quality gate after 3 retries (circuit break):

```json
{
  "chunk_id": 1,
  "page_range": "1-15",
  "final_score": 6,
  "reason": "Translated protected name 'Cinderella' as 'Cô bé Lọ Lem'",
  "retries_exhausted": 3
}
```

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | `int` | Chunk sequence number |
| `page_range` | `str` | Pages covered by this chunk (e.g. `"1-15"`) |
| `final_score` | `int` | Last score from Reviser Agent (1–10) |
| `reason` | `str` | Why the translation failed review |
| `retries_exhausted` | `int` | Number of retries attempted |

---

## Translation Quality Control

### Feedback Loop Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `PASS_SCORE` | `8` | Minimum score to accept a translation |
| `MAX_RETRIES` | `3` | Maximum retry attempts before circuit break |
| `CHUNK_SIZE` | `15` | Pages per translation chunk |

### Scoring Criteria (Reviser Agent)

| Score | Level | Description |
|-------|-------|-------------|
| 9–10 | Excellent | Publication-ready |
| 8 | Good | Acceptable with minor stylistic preferences |
| 6–7 | Acceptable | Notable issues, will trigger retry |
| 4–5 | Poor | Significant errors, will trigger retry |
| 1–3 | Unacceptable | Major constraint violations, will trigger retry |

### Constraint Enforcement

The Translator Agent is bound by these hard rules from `global_metadata`:
- **Protected names** → kept untranslated (e.g. `Cinderella` stays `Cinderella`)
- **Translation fidelity** → `Strict` (no additions/removals) or `Explanatory`
- **Cultural localization** → `false` means keep all references as-is
- **Style register** → language appropriate for target age group
- **SFX handling** → `In_panel_subs`, `Footnotes`, or `Keep`
- **Max drift ratio** → Vietnamese text must stay within N% length of source

---

## Run Locally

```bash
cd phase2

# Install dependencies
pip install -r requirements.txt

# Start the service
uvicorn app.main:app --reload --port 8002

# Run end-to-end test (in another terminal)
python test_flow.py
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | API framework |
| `uvicorn` | ASGI server |
| `httpx` | Async HTTP client (webhook) |
| `pydantic` | Schema validation |
| `google-genai` | Gemini 2.5 Flash API (Translator + Reviser agents) |
| `python-dotenv` | Environment variable loading |
