import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from models.schemas import ContextTransformation
from pipeline.step2.service import run_context_transformation, run_vlm_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline/step2", tags=["Localization Pipeline"])

@router.post(
    "/vlm-analysis",
    summary="Run Step 2: VLM Analysis to get scene context as JSON",
    responses={200: {"content": {"application/json": {}}}},
)
async def step2_vlm_analysis(
    image: UploadFile = File(...),
):
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")
        
    try:
        result = await run_vlm_analysis(contents, image.filename or "input.png")
        return result
    except Exception as e:
        logger.error(f"Step 2 VLM error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/context-transform",
    summary="Run Step 2: Context Transformation independently",
    responses={200: {"content": {"image/png": {}}}},
)
async def step2_context_transform(
    image: UploadFile = File(...),
    target_culture: str = Form(
        default="Vietnamese",
        description='Target culture for localization.',
    ),
    description: Optional[str] = Form(
        default=None,
        description='Optional extra description.',
    ),
    seed: Optional[int] = Form(default=None),
):
    context = ContextTransformation(target_culture=target_culture, description=description)
    
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")
        
    try:
        result = await run_context_transformation(contents, image.filename or "input.png", context, seed)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        logger.error(f"Step 2 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
