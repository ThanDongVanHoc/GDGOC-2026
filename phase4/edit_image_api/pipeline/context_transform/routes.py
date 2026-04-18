import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from models.schemas import BackgroundData
from pipeline.context_transform.service import run_context_transformation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Localization Pipeline"])


@router.post(
    "/context-transform",
    summary="Run Context Transformation independently",
    responses={200: {"content": {"image/png": {}}}},
)
async def context_transform(
    image: UploadFile = File(...),
    scene_type: str = Form(
        ...,
        description="The target scene type, e.g. 'indoor dining room'.",
    ),
    preserved_foreground: list[str] = Form(
        default=[],
        description="Elements to preserve (one per field). E.g. 'the roasted turkey'.",
    ),
    modified_background_elements: list[str] = Form(
        default=[],
        description="Background elements to modify (one per field). E.g. 'the wall decorations'.",
    ),
    vietnamese_setting_suggestions: list[str] = Form(
        default=[],
        description="Vietnamese setting suggestions (one per field).",
    ),
    constraints: list[str] = Form(
        default=[],
        description="Hard generation constraints (one per field).",
    ),
    seed: Optional[int] = Form(default=None),
):
    context = BackgroundData(
        scene_type=scene_type,
        preserved_foreground=preserved_foreground,
        modified_background_elements=modified_background_elements,
        vietnamese_setting_suggestions=vietnamese_setting_suggestions,
        constraints=constraints,
    )

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")

    try:
        result = await run_context_transformation(contents, image.filename or "input.png", context, seed)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        logger.error(f"Context Transformation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
