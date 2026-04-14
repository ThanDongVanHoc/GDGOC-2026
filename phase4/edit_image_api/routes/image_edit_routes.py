"""
Image edit routes – endpoints for AI-powered image editing via ComfyUI.
"""

import os
import json
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

from config import OUTPUTS_DIR
from services.comfyui_service import edit_image

router = APIRouter(prefix="/image-edit", tags=["Image Edit"])

PROMPT_TEMPLATE = (
    "Edit the image realistically by localizing the scene to Vietnam. "
    "Adjust the background to a simple Vietnamese urban environment"
    "{REPLACEMENTS} "
    "Keep all people exactly unchanged, including faces, pose, and expressions. "
    "Preserve the original composition, camera angle, and warm lighting.   "
    "All text in the image must remain completely unchanged, with identical pixels, font, spacing, and position. "
    "Do not modify any text regions. Do not add any overlays, annotations, bounding boxes, or visual markers.  "
    "Do not add any other objects. Output only the final edited image."
)

@router.post(
    "/",
    summary="Edit an image by localizing elements (e.g., hotdog -> hamburger)",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "The edited image in PNG format.",
        }
    },
)
async def edit_image_endpoint(
    image: UploadFile = File(..., description="The source image to edit."),
    replacements_json: str = Form(
        ..., 
        description='JSON string of replacements, e.g. {"hotdog": "hamburger", "hat": "helmet"}'
    ),
    seed: int | None = Form(None, description="Optional random seed for reproducibility."),
):
    """Send an image and localization replacements to ComfyUI (Qwen Image Edit workflow) and return the edited image.

    The edited image is also saved to the outputs/ folder.
    """
    # Parse replacements
    try:
        replacements = json.loads(replacements_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format for replacements.")

    if not isinstance(replacements, dict):
        raise HTTPException(status_code=400, detail="Replacements must be a dictionary.")

    replace_strs = []
    for src, tgt in replacements.items():
        replace_strs.append(f"Replace {src} with {tgt}.")
    
    replacement_text = " ".join(replace_strs)
    final_prompt = PROMPT_TEMPLATE.replace("{REPLACEMENTS}", replacement_text)

    # Read uploaded file
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file.")

    original_filename = image.filename or "input.png"

    try:
        result_bytes = await edit_image(
            image_bytes=contents,
            filename=original_filename,
            prompt=final_prompt,
            seed=seed,
        )
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ComfyUI error: {exc}")

    # Save a copy to outputs/
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(original_filename)[0]
    output_filename = f"{base_name}_edited_{timestamp}.png"
    output_path = os.path.join(OUTPUTS_DIR, output_filename)
    with open(output_path, "wb") as f:
        f.write(result_bytes)

    return Response(
        content=result_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="{output_filename}"',
            "X-Output-Path": output_path,
        },
    )
