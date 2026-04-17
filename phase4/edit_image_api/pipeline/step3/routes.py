import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from models.schemas import TextReplacement
from routes.pipeline_routes import _parse_models
from pipeline.step3.service import run_text_replacement

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline/step3", tags=["Localization Pipeline"])

@router.post(
    "/text-replace",
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
