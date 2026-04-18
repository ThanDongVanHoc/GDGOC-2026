"""
ComfyUI service – upload image, queue qwen-image-edit workflow, poll and download result.
"""

import io
import json
import os
import random
import time
import uuid

import httpx

COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:1234")

# Polling settings
POLL_INTERVAL = 1.0  # seconds
POLL_TIMEOUT = 300   # max seconds to wait


def _load_workflow(workflow_filename: str) -> dict:
    """Load the base workflow JSON from disk."""
    workflow_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workflows", workflow_filename)
    with open(workflow_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def upload_image_to_comfyui(image_bytes: bytes, filename: str) -> str:
    """Upload an image to ComfyUI's /upload/image endpoint.

    Returns the filename stored on the ComfyUI server.
    """
    async with httpx.AsyncClient(base_url=COMFYUI_BASE_URL, timeout=60) as client:
        resp = await client.post(
            "/upload/image",
            files={"image": (filename, image_bytes, "image/png")},
            data={"overwrite": "true"},
        )
        resp.raise_for_status()
        data = resp.json()
        # ComfyUI returns {"name": "filename.png", "subfolder": "", "type": "input"}
        return data["name"]


async def queue_prompt(workflow: dict, client_id: str) -> str:
    """Send a workflow prompt to ComfyUI and return the prompt_id."""
    payload = {
        "prompt": workflow,
        "client_id": client_id,
    }
    async with httpx.AsyncClient(base_url=COMFYUI_BASE_URL, timeout=60) as client:
        resp = await client.post("/prompt", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["prompt_id"]


async def poll_for_completion(prompt_id: str) -> dict:
    """Poll ComfyUI /history/{prompt_id} until the job finishes.

    Returns the history entry for the prompt.
    """
    async with httpx.AsyncClient(base_url=COMFYUI_BASE_URL, timeout=30) as client:
        elapsed = 0.0
        while elapsed < POLL_TIMEOUT:
            resp = await client.get(f"/history/{prompt_id}")
            resp.raise_for_status()
            history = resp.json()
            if prompt_id in history:
                return history[prompt_id]
            await _async_sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

    raise TimeoutError(
        f"ComfyUI did not complete prompt {prompt_id} within {POLL_TIMEOUT}s"
    )


async def _async_sleep(seconds: float):
    """Async-friendly sleep."""
    import asyncio
    await asyncio.sleep(seconds)


async def download_output_image(
    filename: str,
    subfolder: str = "",
    img_type: str = "temp",
) -> bytes:
    """Download an output image from ComfyUI."""
    params = {
        "filename": filename,
        "subfolder": subfolder,
        "type": img_type,
    }
    async with httpx.AsyncClient(base_url=COMFYUI_BASE_URL, timeout=60) as client:
        resp = await client.get("/view", params=params)
        resp.raise_for_status()
        return resp.content


async def edit_image(image_bytes: bytes, filename: str, prompt: str, workflow_filename: str = "qwen-image-edit.json", seed: int | None = None) -> bytes:
    """Full pipeline: upload image → build workflow → queue → poll → download result.

    Args:
        image_bytes: Raw bytes of the input image.
        filename:    Original filename of the image.
        prompt:      Edit instruction (e.g. "Replace the sky with sunset").
        workflow_filename: Name of the workflow JSON file (default: qwen-image-edit.json).
        seed:        Optional random seed. If None a random one is generated.

    Returns:
        bytes of the edited output image (PNG).
    """
    # 1. Upload image to ComfyUI
    uploaded_name = await upload_image_to_comfyui(image_bytes, filename)

    # 2. Load and customise the workflow
    workflow = _load_workflow(workflow_filename)

    # Set input image (node "78")
    workflow["78"]["inputs"]["image"] = uploaded_name

    # Set the edit prompt (node "115:111" – positive conditioning)
    workflow["115:111"]["inputs"]["prompt"] = prompt

    # Set random seed
    if seed is None:
        seed = random.randint(0, 2**53)
    workflow["115:3"]["inputs"]["seed"] = seed

    # 3. Queue the prompt
    client_id = uuid.uuid4().hex
    prompt_id = await queue_prompt(workflow, client_id)

    # 4. Poll for completion
    history_entry = await poll_for_completion(prompt_id)

    # 5. Extract output images from history
    outputs = history_entry.get("outputs", {})
    # The PreviewImage nodes are "124" and "115:116"; grab the first available image
    output_image_info = None
    for node_id in ("124", "115:116"):
        node_output = outputs.get(node_id, {})
        images = node_output.get("images", [])
        if images:
            output_image_info = images[0]
            break

    if output_image_info is None:
        raise RuntimeError(
            f"No output images found in ComfyUI history for prompt {prompt_id}"
        )

    # 6. Download the result
    result_bytes = await download_output_image(
        filename=output_image_info["filename"],
        subfolder=output_image_info.get("subfolder", ""),
        img_type=output_image_info.get("type", "temp"),
    )

    return result_bytes
