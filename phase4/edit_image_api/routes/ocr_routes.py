"""
OCR routes – endpoints for text detection.
"""

import os
from datetime import datetime

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse

from config import OUTPUTS_DIR
from services.ocr_service import get_reader, draw_bounding_boxes

router = APIRouter()


@router.post("/detect-text")
async def detect_text(image: UploadFile = File(...)):
    """Detect text regions in an uploaded image.

    Returns:
        - `bounding_boxes`: list of detected text regions with coordinates,
          detected text, and confidence score.
        - `output_image`: path to the annotated image saved in outputs/ folder.
    """
    # Read the uploaded image
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid image file. Could not decode the image."},
        )

    # Run OCR detection
    reader = get_reader()
    results = reader.readtext(img_bgr)

    # Build bounding boxes response
    bounding_boxes = []
    for bbox, text, confidence in results:
        bounding_boxes.append(
            {
                "bbox": [[int(pt[0]), int(pt[1])] for pt in bbox],
                "text": text,
                "confidence": round(float(confidence), 4),
            }
        )

    # Draw bounding boxes on the image
    annotated_img = draw_bounding_boxes(img_bgr, results)

    # Save annotated image to outputs/ folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = os.path.splitext(image.filename or "image")[0]
    output_filename = f"{original_name}_{timestamp}.png"
    output_path = os.path.join(OUTPUTS_DIR, output_filename)
    cv2.imwrite(output_path, annotated_img)

    return {
        "total_detections": len(bounding_boxes),
        "bounding_boxes": bounding_boxes,
        "output_image": output_path,
    }


@router.get("/")
async def root():
    """Health check / landing page."""
    return {
        "service": "Text Bounding Box Detector",
        "usage": "POST /detect-text with an image file to detect text regions.",
        "docs": "/docs",
    }
