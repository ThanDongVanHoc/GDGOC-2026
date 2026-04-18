"""
Pipeline routes — endpoints for the 3-step localization pipeline.

POST /pipeline/localize
  - Accepts: image file + explicit background/object/text fields
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
    BackgroundData,
    TextReplacement,
)
from pipeline.localize_pipeline import run_localize_pipeline

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
    description="""\
**3-Step Image Localization Pipeline:**

1. **Context Transformation** — Adjust background/scene to Vietnamese setting
2. **Object Replacement** — Replace specific objects using AI inpainting
3. **Text Replacement** — Remove original text and render Vietnamese text

Each step can be independently skipped by leaving its fields empty.

**Background fields:** Fill in `scene_type` and the list fields to run context transformation.

**Object replacement fields:** Fill `original_objects` and `replacement_objects` (parallel lists).

**Text replacement:** Provide `texts_json` as a JSON array string.
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
    # ── Context Transformation fields ──
    scene_type: Optional[str] = Form(
        default=None,
        description="Target scene type (e.g. 'indoor dining room'). Leave empty to skip context transformation.",
    ),
    preserved_foreground: list[str] = Form(
        default=[],
        description="Foreground elements to preserve (one per field).",
    ),
    modified_background_elements: list[str] = Form(
        default=[],
        description="Background elements to modify (one per field).",
    ),
    vietnamese_setting_suggestions: list[str] = Form(
        default=[],
        description="Vietnamese setting suggestions (one per field).",
    ),
    constraints: list[str] = Form(
        default=[],
        description="Hard generation constraints (one per field).",
    ),
    # ── Object Replacement fields ──
    original_objects: list[str] = Form(
        default=[],
        description="Original object names to replace (one per field). Must pair with replacement_objects.",
    ),
    replacement_objects: list[str] = Form(
        default=[],
        description="Replacement object names (one per field). Must pair with original_objects.",
    ),
    # ── Text Replacement (JSON) ──
    texts_json: Optional[str] = Form(
        default=None,
        description='JSON array of text replacements. Example: [{"bbox": [50,50,250,80], "original_text": "Hello", "new_text": "Xin chào"}]',
    ),
    seed: Optional[int] = Form(default=None, description="Random seed for reproducibility."),
):
    """Run the full localization pipeline on an uploaded image."""

    # Build BackgroundData if scene_type is provided
    background = None
    if scene_type:
        background = BackgroundData(
            scene_type=scene_type,
            preserved_foreground=preserved_foreground,
            modified_background_elements=modified_background_elements,
            vietnamese_setting_suggestions=vietnamese_setting_suggestions,
            constraints=constraints,
        )

    # Build object_replacements dict from parallel lists
    if len(original_objects) != len(replacement_objects):
        raise HTTPException(
            status_code=400,
            detail=f"original_objects ({len(original_objects)}) and replacement_objects ({len(replacement_objects)}) must have the same length.",
        )
    object_replacements = dict(zip(original_objects, replacement_objects))

    # Parse texts
    texts = _parse_models(texts_json, "texts_json", TextReplacement, is_list=True)

    request = LocalizePipelineRequest(
        background=background,
        object_replacements=object_replacements,
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
    # ── Context Transformation fields ──
    scene_type: Optional[str] = Form(
        default=None,
        description="Target scene type. Leave empty to skip context transformation.",
    ),
    preserved_foreground: list[str] = Form(
        default=[],
        description="Foreground elements to preserve (one per field).",
    ),
    modified_background_elements: list[str] = Form(
        default=[],
        description="Background elements to modify (one per field).",
    ),
    vietnamese_setting_suggestions: list[str] = Form(
        default=[],
        description="Vietnamese setting suggestions (one per field).",
    ),
    constraints: list[str] = Form(
        default=[],
        description="Hard generation constraints (one per field).",
    ),
    # ── Object Replacement fields ──
    original_objects: list[str] = Form(
        default=[],
        description="Original object names to replace (one per field).",
    ),
    replacement_objects: list[str] = Form(
        default=[],
        description="Replacement object names (one per field).",
    ),
    # ── Text Replacement (JSON) ──
    texts_json: Optional[str] = Form(
        default=None,
        description='JSON array of text replacements.',
    ),
    seed: Optional[int] = Form(default=None, description="Random seed for reproducibility."),
):
    """Same as /pipeline/localize but returns JSON metadata instead of image bytes."""

    background = None
    if scene_type:
        background = BackgroundData(
            scene_type=scene_type,
            preserved_foreground=preserved_foreground,
            modified_background_elements=modified_background_elements,
            vietnamese_setting_suggestions=vietnamese_setting_suggestions,
            constraints=constraints,
        )

    if len(original_objects) != len(replacement_objects):
        raise HTTPException(
            status_code=400,
            detail=f"original_objects ({len(original_objects)}) and replacement_objects ({len(replacement_objects)}) must have the same length.",
        )
    object_replacements = dict(zip(original_objects, replacement_objects))

    texts = _parse_models(texts_json, "texts_json", TextReplacement, is_list=True)

    request = LocalizePipelineRequest(
        background=background,
        object_replacements=object_replacements,
        texts=texts,
        seed=seed,
    )

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


# ── Individual step endpoints have been moved to their respective step routes.
