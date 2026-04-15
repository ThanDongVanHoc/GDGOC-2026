"""
Phase 4 — Image Processing & Localization API

Services:
  - OCR: Text detection (EasyOCR)
  - Image Edit: Single-shot AI editing (ComfyUI/Qwen)
  - Pipeline: 3-step localization (Object Replace → Context Transform → Text Replace)
"""

import logging

from fastapi import FastAPI

from routes.ocr_routes import router as ocr_router
from routes.image_edit_routes import router as image_edit_router
from routes.pipeline_routes import router as pipeline_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

app = FastAPI(
    title="Phase 4 — Image Localization API",
    description=(
        "3-step image localization pipeline:\n"
        "1. Object Replacement (AI inpainting)\n"
        "2. Context Transformation (AI scene edit)\n"
        "3. Text Replacement (code-based, accurate Vietnamese diacritics)\n\n"
        "Also includes OCR detection and single-shot image editing."
    ),
    version="2.0.0",
)

app.include_router(ocr_router)
app.include_router(image_edit_router)
app.include_router(pipeline_router)
