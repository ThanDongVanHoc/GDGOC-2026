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

STEP2_DIR = Path(__file__).parent

def _build_context_prompt(ctx: ContextTransformation) -> str:
    """Build a prompt for context transformation."""
    with open(STEP2_DIR / "prompt_positive.txt", "r", encoding="utf-8") as f:
        template = f.read().strip()
        
    description_text = f"Specifically: {ctx.description}. " if ctx.description else ""
        
    return template.format(
        target_culture=ctx.target_culture,
        description_text=description_text
    )

def _build_negative_prompt() -> str:
    """Negative prompt for context transformation."""
    with open(STEP2_DIR / "prompt_negative.txt", "r", encoding="utf-8") as f:
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
    workflow = _load_workflow("qwen-image-edit.json")
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


async def run_vlm_analysis(
    image_bytes: bytes,
    filename: str,
) -> dict:
    """Run the VLM analysis workflow to extract JSON for scene context using FPT AI.

    Args:
        image_bytes: Current image as bytes.
        filename: Filename for upload.

    Returns:
        Dictionary containing the parsed JSON from VLM output.
    """
    logger.info("Step 2: Running VLM analysis workflow via FPT AI API...")

    import base64
    import httpx
    import json
    import re

    # 1. Read instruction from file
    instruction = ""
    instruction_path = STEP2_DIR / "vlm_instruction.txt"
    if instruction_path.exists():
        with open(instruction_path, "r", encoding="utf-8") as f:
            instruction = f.read().strip()
    
    if not instruction:
        instruction = "Describe the image background in JSON format."

    # 2. Encode image to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    mime_type = "image/png"
    if filename.lower().endswith(('.jpg', '.jpeg')):
        mime_type = "image/jpeg"
    image_url = f"data:{mime_type};base64,{base64_image}"

    # 3. Prepare FPT AI request payload
    fpt_api_key = os.getenv("FPT_AI_API_KEY", "your-api-key")  # Get from env, or user will provide
    url = "https://mkp-api.fptcloud.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {fpt_api_key}"
    }
    payload = {
        "model": "FPT.AI-KIE-v1.7",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": instruction
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    }
                ]
            }
        ],
        "temperature": 1,
        "max_tokens": 1024,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "stream": False  # Use non-streaming for easier parsing to dictionary
    }

    # 4. Send request
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            resp_data = response.json()
            
            # Extract content text from OpenAI-compatible response
            content = ""
            if "choices" in resp_data and len(resp_data["choices"]) > 0:
                message = resp_data["choices"][0].get("message", {})
                content = message.get("content", "")
            else:
                logger.error(f"Unexpected FPT API response format: {resp_data}")
                return {"raw_output": str(resp_data), "error": "Invalid response format"}

            # Parse JSON out of content
            try:
                # Try to extract from json code block if present
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
                if match:
                    content = match.group(1)
                return json.loads(content)
            except Exception as e:
                logger.error(f"Failed to parse JSON from FPT output: {e}, raw string: {content}")
                return {"raw_output": content, "error": "Failed to parse JSON"}

    except Exception as e:
        logger.error(f"Failed calling FPT API: {e}", exc_info=True)
        return {"error": f"FPT API call failed: {str(e)}"}
