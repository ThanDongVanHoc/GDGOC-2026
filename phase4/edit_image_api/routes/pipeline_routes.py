"""
Pipeline routes — endpoints for the 3-step localization pipeline.

POST /pipeline/localize
  - Accepts: image file + 3 separate JSON fields (objects, context, texts)
  - Returns: edited image (PNG) + pipeline metadata in headers
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from config import OUTPUTS_DIR
from models.schemas import (
    LocalizePipelineRequest,
    LocalizePipelineResponse,
    ObjectReplacement,
    ContextTransformation,
    TextReplacement,
)
from pipeline.localize_pipeline import run_localize_pipeline
from pipeline.step1_object_replace import run_object_replacement
from pipeline.step2_context_transform import run_context_transformation
from pipeline.step3_text_replace import run_text_replacement

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Localization Pipeline"])


def _parse_json_field(raw: str | None, field_name: str) -> any:
    """Parse a JSON string field, returning None if empty/null."""
    if raw is None or raw.strip() == "" or raw.strip().lower() == "null":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON format for '{field_name}'.",
        )


@router.post(
    "/localize",
    summary="Run 3-step image localization pipeline",
    description="""
**3-Step Image Localization Pipeline:**

1. **Object Replacement** — Replace specific objects using AI inpainting
2. **Context Transformation** — Adjust background/scene to Vietnamese setting
3. **Text Replacement** — Remove original text and render Vietnamese text

Each step can be independently skipped by leaving its field empty or null.

**Example fields:**

`objects_json`:
```json
[
    {"bbox": [100, 200, 300, 400], "original": "hamburger", "replacement": "bánh chưng"}
]
```

`context_json`:
```json
{"target_culture": "Vietnamese", "description": "Vietnamese street food stall", "strength": 0.5}
```

`texts_json`:
```json
[
    {"bbox": [50, 50, 250, 80], "original_text": "Hello World", "new_text": "Xin chào thế giới"}
]
```
    """,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "The localized image in PNG format.",
        }
    },
)
async def localize_image(
    image: UploadFile = File(..., description="The source image to localize."),
    objects_json: Optional[str] = Form(
        default=None,
        description='JSON array of objects to replace.',
        openapi_examples={"example": {"value": '[{"bbox": [100, 200, 300, 400], "original": "hamburger", "replacement": "bánh chưng"}]'}},
    ),
    context_json: Optional[str] = Form(
        default=None,
        description='JSON object for context transformation.',
        openapi_examples={"example": {"value": '{"target_culture": "Vietnamese", "description": "street food stall", "strength": 0.5}'}},
    ),
    texts_json: Optional[str] = Form(
        default=None,
        description='JSON array of text replacements.',
        openapi_examples={"example": {"value": '[{"bbox": [50, 50, 250, 80], "original_text": "Hello World", "new_text": "Xin chào"}]'}},
    ),
    seed: Optional[int] = Form(default=None, description="Random seed for reproducibility."),
):
    """Run the full localization pipeline on an uploaded image."""

    # ── Parse each field independently ──────────────────────────────────
    # Objects
    objects_raw = _parse_json_field(objects_json, "objects_json")
    objects = []
    if objects_raw is not None:
        if not isinstance(objects_raw, list):
            raise HTTPException(status_code=400, detail="objects_json must be a JSON array.")
        try:
            objects = [ObjectReplacement(**obj) for obj in objects_raw]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid objects_json: {e}")

    # Context
    context_raw = _parse_json_field(context_json, "context_json")
    context = None
    if context_raw is not None:
        if not isinstance(context_raw, dict):
            raise HTTPException(status_code=400, detail="context_json must be a JSON object.")
        try:
            context = ContextTransformation(**context_raw)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid context_json: {e}")

    # Texts
    texts_raw = _parse_json_field(texts_json, "texts_json")
    texts = []
    if texts_raw is not None:
        if not isinstance(texts_raw, list):
            raise HTTPException(status_code=400, detail="texts_json must be a JSON array.")
        try:
            texts = [TextReplacement(**txt) for txt in texts_raw]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid texts_json: {e}")

    # Build pipeline request
    request = LocalizePipelineRequest(
        objects=objects,
        context=context,
        texts=texts,
        seed=seed,
    )

    # ── Read image ──────────────────────────────────────────────────────
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")

    original_filename = image.filename or "input.png"

    # ── Run pipeline ────────────────────────────────────────────────────
    try:
        result_bytes, pipeline_response = await run_localize_pipeline(
            image_bytes=contents,
            filename=original_filename,
            request=request,
            save_intermediates=True,
        )
    except Exception as exc:
        logger.error(f"Pipeline error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    # Build response headers with pipeline metadata
    steps_summary = " | ".join(
        f"{s.step}: {s.status} ({s.duration_seconds}s)" for s in pipeline_response.steps
    )

    return Response(
        content=result_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="localized_{original_filename}"',
            "X-Pipeline-Status": pipeline_response.status,
            "X-Pipeline-Steps": steps_summary,
            "X-Pipeline-Duration": str(pipeline_response.total_duration_seconds),
            "X-Output-Path": pipeline_response.output_path or "",
        },
    )


@router.post(
    "/localize/json",
    summary="Run pipeline and return JSON response (with image path)",
    response_model=LocalizePipelineResponse,
)
async def localize_image_json(
    image: UploadFile = File(..., description="The source image to localize."),
    objects_json: Optional[str] = Form(
        default=None,
        description='JSON array of objects to replace.',
        openapi_examples={"example": {"value": '[{"bbox": [100, 200, 300, 400], "original": "hamburger", "replacement": "bánh chưng"}]'}},
    ),
    context_json: Optional[str] = Form(
        default=None,
        description='JSON object for context transformation.',
        openapi_examples={"example": {"value": '{"target_culture": "Vietnamese", "strength": 0.5}'}},
    ),
    texts_json: Optional[str] = Form(
        default=None,
        description='JSON array of text replacements.',
        openapi_examples={"example": {"value": '[{"bbox": [50, 50, 250, 80], "original_text": "Hello", "new_text": "Xin chào"}]'}},
    ),
    seed: Optional[int] = Form(default=None, description="Random seed for reproducibility."),
):
    """Same as /pipeline/localize but returns JSON metadata instead of image bytes."""

    # Parse fields (same logic)
    objects_raw = _parse_json_field(objects_json, "objects_json")
    objects = []
    if objects_raw is not None:
        if not isinstance(objects_raw, list):
            raise HTTPException(status_code=400, detail="objects_json must be a JSON array.")
        objects = [ObjectReplacement(**obj) for obj in objects_raw]

    context_raw = _parse_json_field(context_json, "context_json")
    context = None
    if context_raw is not None:
        if not isinstance(context_raw, dict):
            raise HTTPException(status_code=400, detail="context_json must be a JSON object.")
        context = ContextTransformation(**context_raw)

    texts_raw = _parse_json_field(texts_json, "texts_json")
    texts = []
    if texts_raw is not None:
        if not isinstance(texts_raw, list):
            raise HTTPException(status_code=400, detail="texts_json must be a JSON array.")
        texts = [TextReplacement(**txt) for txt in texts_raw]

    request = LocalizePipelineRequest(objects=objects, context=context, texts=texts, seed=seed)

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")

    original_filename = image.filename or "input.png"

    try:
        _, pipeline_response = await run_localize_pipeline(
            image_bytes=contents,
            filename=original_filename,
            request=request,
            save_intermediates=True,
        )
    except Exception as exc:
        logger.error(f"Pipeline error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    return pipeline_response


# ── Individual Step Endpoints ───────────────────────────────────────────────

@router.post(
    "/step1/object-replace",
    summary="Run Step 1: Object Replacement independently",
    responses={200: {"content": {"image/png": {}}}},
)
async def step1_object_replace(
    image: UploadFile = File(...),
    objects_json: str = Form(
        ...,
        description='JSON array of objects to replace.\n\nExample:\n```json\n[{"bbox": [100, 200, 300, 400], "original": "hamburger", "replacement": "bánh chưng"}]\n```',
        json_schema_extra={"example": '[{"bbox": [100, 200, 300, 400], "original": "hamburger", "replacement": "bánh chưng"}]'}
    ),
    seed: Optional[int] = Form(default=None),
):
    objects_raw = _parse_json_field(objects_json, "objects_json")
    if not isinstance(objects_raw, list):
        raise HTTPException(status_code=400, detail="objects_json must be a JSON array.")
    try:
        objects = [ObjectReplacement(**obj) for obj in objects_raw]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid objects: {e}")

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")

    try:
        result_bytes = await run_object_replacement(
            image_bytes=contents,
            filename=image.filename or "input.png",
            objects=objects,
            seed=seed,
        )
    except Exception as exc:
        logger.error(f"Step 1 error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Step 1 error: {exc}")

    return Response(content=result_bytes, media_type="image/png")


@router.post(
    "/step2/context-transform",
    summary="Run Step 2: Context Transformation independently",
    responses={200: {"content": {"image/png": {}}}},
)
async def step2_context_transform(
    image: UploadFile = File(...),
    context_json: str = Form(
        ...,
        description='JSON object for context transformation.\n\nExample:\n```json\n{"target_culture": "Vietnamese", "description": "street stall", "strength": 0.5}\n```',
        json_schema_extra={"example": '{"target_culture": "Vietnamese", "description": "street stall", "strength": 0.5}'}
    ),
    seed: Optional[int] = Form(default=None),
):
    context_raw = _parse_json_field(context_json, "context_json")
    if not isinstance(context_raw, dict):
        raise HTTPException(status_code=400, detail="context_json must be a JSON object.")
    try:
        context = ContextTransformation(**context_raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid context: {e}")

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")

    try:
        result_bytes = await run_context_transformation(
            image_bytes=contents,
            filename=image.filename or "input.png",
            context=context,
            seed=seed,
        )
    except Exception as exc:
        logger.error(f"Step 2 error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Step 2 error: {exc}")

    return Response(content=result_bytes, media_type="image/png")


@router.post(
    "/step3/text-replace",
    summary="Run Step 3: Text Replacement independently",
    responses={200: {"content": {"image/png": {}}}},
)
async def step3_text_replace(
    image: UploadFile = File(...),
    texts_json: str = Form(
        ...,
        description='JSON array of text replacements.\n\nExample:\n```json\n[{"bbox": [50, 50, 250, 80], "original_text": "Hello World", "new_text": "Xin chào"}]\n```',
        json_schema_extra={"example": '[{"bbox": [50, 50, 250, 80], "original_text": "Hello World", "new_text": "Xin chào"}]'}
    ),
):
    texts_raw = _parse_json_field(texts_json, "texts_json")
    if not isinstance(texts_raw, list):
        raise HTTPException(status_code=400, detail="texts_json must be a JSON array.")
    try:
        texts = [TextReplacement(**txt) for txt in texts_raw]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid texts: {e}")

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")

    try:
        result_bytes = await run_text_replacement(
            image_bytes=contents,
            texts=texts,
        )
    except Exception as exc:
        logger.error(f"Step 3 error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Step 3 error: {exc}")

    return Response(content=result_bytes, media_type="image/png")

