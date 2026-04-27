"""
Object Replacement — Replace specific objects in the image using
ComfyUI inpainting (Qwen Image Edit).

All replacement pairs are combined into a single prompt and sent once.
"""

import logging
import random
import uuid

from typing import Dict
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

OBJECT_REPLACE_DIR = Path(__file__).parent


def _build_object_prompt(object_replacements: Dict[str, str]) -> str:
    """Build a single prompt containing all object replacement instructions."""
    with open(OBJECT_REPLACE_DIR / "prompt_positive.txt", "r", encoding="utf-8") as f:
        template = f.read().strip()

    lines = [f"Replace the {orig} with {repl}." for orig, repl in object_replacements.items()]
    replacement_instructions = "\n".join(lines)

    return template.format(replacement_instructions=replacement_instructions)


def _build_negative_prompt() -> str:
    """Negative prompt to avoid common artifacts."""
    with open(OBJECT_REPLACE_DIR / "prompt_negative.txt", "r", encoding="utf-8") as f:
        return f.read().strip()


async def run_object_replacement(
    image_bytes: bytes,
    filename: str,
    object_replacements: Dict[str, str],
    seed: int | None = None,
) -> bytes:
    """Replace all objects in a single pass using ComfyUI.

    Args:
        image_bytes: Current image as bytes.
        filename: Filename for upload.
        object_replacements: Dictionary mapping original object to replacement.
        seed: Optional seed for reproducibility.

    Returns:
        Updated image bytes with all objects replaced.
    """
    if not object_replacements:
        logger.info("[Object Replacement] No objects to replace — skipping.")
        return image_bytes

    pairs_str = ", ".join(f"'{k}' → '{v}'" for k, v in object_replacements.items())
    logger.info(f"[Object Replacement] Replacing {len(object_replacements)} object(s) in one pass: {pairs_str}")

    used_seed = seed if seed is not None else random.randint(0, 2**53)

    # Upload image
    uploaded_name = await upload_image_to_comfyui(
        image_bytes,
        f"obj_{filename}",
    )

    # Build workflow with combined prompt
    workflow = _load_workflow("qwen-image-edit.json")
    workflow["78"]["inputs"]["image"] = uploaded_name
    workflow["115:111"]["inputs"]["prompt"] = _build_object_prompt(object_replacements)
    workflow["115:110"]["inputs"]["prompt"] = _build_negative_prompt()
    workflow["115:3"]["inputs"]["seed"] = used_seed

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
        raise RuntimeError("[Object Replacement] No output image from object replacement.")

    result_bytes = await download_output_image(
        filename=output_image_info["filename"],
        subfolder=output_image_info.get("subfolder", ""),
        img_type=output_image_info.get("type", "temp"),
    )

    logger.info("[Object Replacement] All objects replaced successfully in one pass.")
    return result_bytes
