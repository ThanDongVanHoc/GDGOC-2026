"""
Step 1: Object Replacement — Replace specific objects in the image using
ComfyUI inpainting (Qwen Image Edit).

For each object:
  1. Build a focused prompt targeting only that object's bbox
  2. Send to ComfyUI for inpainting
  3. Use the result as input for the next object

Objects are processed sequentially to avoid conflicts.
"""

import logging
import random

from models.schemas import ObjectReplacement
from services.comfyui_service import (
    upload_image_to_comfyui,
    queue_prompt,
    poll_for_completion,
    download_output_image,
    _load_workflow,
)

logger = logging.getLogger(__name__)


import os
from pathlib import Path

STEP1_DIR = Path(__file__).parent

def _build_object_prompt(obj: ObjectReplacement) -> str:
    """Build a focused inpainting prompt for a single object replacement."""
    x1, y1, x2, y2 = obj.bbox
    
    with open(STEP1_DIR / "prompt_positive.txt", "r", encoding="utf-8") as f:
        template = f.read().strip()
        
    return template.format(
        original=obj.original,
        replacement=obj.replacement,
        x1=x1, y1=y1, x2=x2, y2=y2
    )

def _build_negative_prompt() -> str:
    """Negative prompt to avoid common artifacts."""
    with open(STEP1_DIR / "prompt_negative.txt", "r", encoding="utf-8") as f:
        return f.read().strip()


async def run_object_replacement(
    image_bytes: bytes,
    filename: str,
    objects: list[ObjectReplacement],
    seed: int | None = None,
) -> bytes:
    """Replace objects one-by-one using ComfyUI.

    Args:
        image_bytes: Current image as bytes.
        filename: Filename for upload.
        objects: List of objects to replace.
        seed: Optional seed for reproducibility.

    Returns:
        Updated image bytes with all objects replaced.
    """
    if not objects:
        logger.info("Step 1: No objects to replace — skipping.")
        return image_bytes

    current_bytes = image_bytes
    base_seed = seed if seed is not None else random.randint(0, 2**53)

    for i, obj in enumerate(objects):
        logger.info(
            f"Step 1: Replacing object {i + 1}/{len(objects)}: "
            f"'{obj.original}' → '{obj.replacement}' at bbox {obj.bbox}"
        )

        # Upload current image
        uploaded_name = await upload_image_to_comfyui(
            current_bytes,
            f"step1_obj{i}_{filename}",
        )

        # Build workflow with focused prompt
        workflow = _load_workflow("qwen-image-edit.json")
        workflow["78"]["inputs"]["image"] = uploaded_name
        workflow["115:111"]["inputs"]["prompt"] = _build_object_prompt(obj)
        workflow["115:110"]["inputs"]["prompt"] = _build_negative_prompt()
        workflow["115:3"]["inputs"]["seed"] = base_seed + i

        # Queue and wait
        import uuid
        client_id = uuid.uuid4().hex
        prompt_id = await queue_prompt(workflow, client_id)
        history = await poll_for_completion(prompt_id)

        # Extract output
        outputs = history.get("outputs", {})
        output_image_info = None
        for node_id in ("124", "115:116"):
            node_output = outputs.get(node_id, {})
            images = node_output.get("images", [])
            if images:
                output_image_info = images[0]
                break

        if output_image_info is None:
            raise RuntimeError(
                f"Step 1: No output for object {i + 1} "
                f"('{obj.original}' → '{obj.replacement}')"
            )

        current_bytes = await download_output_image(
            filename=output_image_info["filename"],
            subfolder=output_image_info.get("subfolder", ""),
            img_type=output_image_info.get("type", "temp"),
        )

        logger.info(f"Step 1: Object {i + 1}/{len(objects)} replaced successfully.")

    return current_bytes
