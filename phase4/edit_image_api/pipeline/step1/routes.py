import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from models.schemas import ObjectReplacement
from routes.pipeline_routes import _parse_models
from pipeline.step1.service import run_object_replacement

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline/step1", tags=["Localization Pipeline"])

@router.post(
    "/object-replace",
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
