"""
Step 2: Context Transformation — Change the background/scene context
to match the target culture (Vietnamese) using ComfyUI (Qwen Image Edit).

Strategy:
  - Use a gentle prompt to shift the scene context while preserving characters,
    composition, and overall layout.
  - Characters/people are explicitly protected in the prompt.
"""

import logging
import random
import uuid

from models.schemas import ContextTransformation
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

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def _build_context_prompt(ctx: ContextTransformation) -> str:
    """Build a prompt for context transformation."""
    with open(PROMPTS_DIR / "step2_context_positive.txt", "r", encoding="utf-8") as f:
        template = f.read().strip()
        
    description_text = f"Specifically: {ctx.description}. " if ctx.description else ""
        
    return template.format(
        target_culture=ctx.target_culture,
        description_text=description_text
    )

def _build_negative_prompt() -> str:
    """Negative prompt for context transformation."""
    with open(PROMPTS_DIR / "step2_context_negative.txt", "r", encoding="utf-8") as f:
        return f.read().strip()


async def run_context_transformation(
    image_bytes: bytes,
    filename: str,
    context: ContextTransformation | None,
    seed: int | None = None,
) -> bytes:
    """Transform the scene context/background.

    Args:
        image_bytes: Current image as bytes.
        filename: Filename for upload.
        context: Context transformation config. None = skip.
        seed: Optional seed for reproducibility.

    Returns:
        Updated image bytes with transformed context.
    """
    if context is None:
        logger.info("Step 2: No context transformation requested — skipping.")
        return image_bytes

    logger.info(
        f"Step 2: Transforming context to '{context.target_culture}'"
    )

    # Upload current image
    uploaded_name = await upload_image_to_comfyui(
        image_bytes,
        f"step2_ctx_{filename}",
    )

    # Build workflow
    workflow = _load_workflow()
    workflow["78"]["inputs"]["image"] = uploaded_name
    workflow["115:111"]["inputs"]["prompt"] = _build_context_prompt(context)
    workflow["115:110"]["inputs"]["prompt"] = _build_negative_prompt()

    # Queue and wait
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
        raise RuntimeError("Step 2: No output image from context transformation.")

    result_bytes = await download_output_image(
        filename=output_image_info["filename"],
        subfolder=output_image_info.get("subfolder", ""),
        img_type=output_image_info.get("type", "temp"),
    )

    logger.info("Step 2: Context transformation completed successfully.")
    return result_bytes
