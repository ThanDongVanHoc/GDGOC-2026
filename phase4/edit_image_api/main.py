"""
Phase 4 — Image Processing & Localization API

Services:
  - OCR: Text detection (EasyOCR)
  - Image Edit: Single-shot AI editing (ComfyUI/Qwen)
  - Pipeline: 3-step localization (Object Replace → Context Transform → Text Replace)
"""

import logging

from fastapi import FastAPI

from routes.image_edit_routes import router as image_edit_router
from routes.pipeline_routes import router as pipeline_router
from pipeline.step1.routes import router as step1_router
from pipeline.step2.routes import router as step2_router
from pipeline.step3.routes import router as step3_router

import os
from logging.handlers import RotatingFileHandler

# Configure root logger for console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)

# Configure dedicated file handler for pipeline logs
os.makedirs("logs", exist_ok=True)
pipeline_file_handler = RotatingFileHandler("logs/pipeline.log", maxBytes=5*1024*1024, backupCount=2)
pipeline_file_handler.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s"))

# Attach file handler to pipeline-related loggers
logging.getLogger("pipeline").addHandler(pipeline_file_handler)
logging.getLogger("routes.pipeline_routes").addHandler(pipeline_file_handler)

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

app.include_router(image_edit_router)
app.include_router(pipeline_router)
app.include_router(step1_router)
app.include_router(step2_router)
app.include_router(step3_router)
