"""
FastAPI Text Detection API
- Receives an image
- Returns bounding boxes of all detected text regions
- Saves an annotated image with bounding boxes to outputs/ folder
"""

from fastapi import FastAPI

from routes.ocr_routes import router as ocr_router
from routes.image_edit_routes import router as image_edit_router

app = FastAPI(
    title="Image Processing API",
    description="Text detection and AI-powered image editing via ComfyUI.",
    version="1.1.0",
)

app.include_router(ocr_router)
app.include_router(image_edit_router)
