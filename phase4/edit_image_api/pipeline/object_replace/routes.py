import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

import json

from pipeline.object_replace.service import run_object_replacement

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Localization Pipeline"])

@router.post(
    "/object-replace",
    summary="Run Object Replacement independently",
    responses={200: {"content": {"image/png": {}}}},
)
async def object_replace(
    image: UploadFile = File(...),
    objects_json: str = Form(
        ...,
        description='JSON dictionary of objects to replace.\n\nExample:\n```json\n{"snowman": "sandcastle"}\n```',
        json_schema_extra={"example": '{"snowman": "sandcastle"}'}
    ),
    seed: Optional[int] = Form(default=None),
):
    try:
        objects = json.loads(objects_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for 'objects_json'.")
    
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")
        
    try:
        result = await run_object_replacement(contents, image.filename or "input.png", objects, seed)
        return Response(content=result, media_type="image/png")
    except Exception as e:
        logger.error(f"Step 1 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
