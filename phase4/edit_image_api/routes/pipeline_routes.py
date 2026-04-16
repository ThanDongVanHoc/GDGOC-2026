"""
Pipeline routes — endpoints for the 3-step localization pipeline.

POST /pipeline/localize
  - Accepts: image file + 3 separate JSON fields (objects, context, texts)
  - Returns: edited image (PNG) + pipeline metadata in headers
"""

import json
import logging
from typing import Optional, Type, TypeVar, Any

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


T = TypeVar('T')

def _parse_models(raw: str | None, field_name: str, model_class: Type[T], is_list: bool) -> Any:
    """Parse a JSON string field into Pydantic models."""
    if raw is None or raw.strip() == "" or raw.strip().lower() == "null":
        return [] if is_list else None
        
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format for '{field_name}'.")

    if is_list:
        if not isinstance(data, list):
            raise HTTPException(status_code=400, detail=f"{field_name} must be a JSON array.")
        try:
            return [model_class(**item) for item in data]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid {field_name}: {e}")
    else:
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail=f"{field_name} must be a JSON object.")
        try:
            return model_class(**data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid {field_name}: {e}")


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

    objects = _parse_models(objects_json, "objects_json", ObjectReplacement, is_list=True)
    context = _parse_models(context_json, "context_json", ContextTransformation, is_list=False)
    texts = _parse_models(texts_json, "texts_json", TextReplacement, is_list=True)

    request = LocalizePipelineRequest(
        objects=objects,
        context=context,
        texts=texts,
        seed=seed,
    )

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")

    original_filename = image.filename or "input.png"

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

    objects = _parse_models(objects_json, "objects_json", ObjectReplacement, is_list=True)
    context = _parse_models(context_json, "context_json", ContextTransformation, is_list=False)
    texts = _parse_models(texts_json, "texts_json", TextReplacement, is_list=True)

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
    objects = _parse_models(objects_json, "objects_json", ObjectReplacement, is_list=True)
    
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")
        
    try:
        result = await run_object_replacement(contents, image.filename or "input.png", objects, seed)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        logger.error(f"Step 1 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    context = _parse_models(context_json, "context_json", ContextTransformation, is_list=False)
    
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")
        
    try:
        result = await run_context_transformation(contents, image.filename or "input.png", context, seed)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        logger.error(f"Step 2 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
    texts = _parse_models(texts_json, "texts_json", TextReplacement, is_list=True)
    
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")
        
    try:
        result = await run_text_replacement(contents, texts)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        logger.error(f"Step 3 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
