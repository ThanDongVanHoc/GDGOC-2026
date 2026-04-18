"""
Localize Pipeline — Orchestrates the 3-step image localization process.

Pipeline flow:
  Step 1: Object Replacement   (ComfyUI inpainting)
  Step 2: Context Transformation (ComfyUI style transfer)
  Step 3: Text Replacement      (cv2 inpaint + PIL render)

Each step receives the output image from the previous step.
Steps can be skipped if their input data is empty/None.
Intermediate results are saved for debugging.
"""

import logging
import os
import time
from datetime import datetime

from config import OUTPUTS_DIR
from models.schemas import (
    LocalizePipelineRequest,
    LocalizePipelineResponse,
    StepResult,
)
from pipeline.object_replace.service import run_object_replacement
from pipeline.context_transform.service import run_context_transformation
from pipeline.text_replace.service import run_text_replacement

logger = logging.getLogger(__name__)

# Directory for intermediate pipeline results (debugging)
INTERMEDIATE_DIR = os.path.join(OUTPUTS_DIR, "pipeline_intermediate")
os.makedirs(INTERMEDIATE_DIR, exist_ok=True)


def _save_intermediate(image_bytes: bytes, step_name: str, run_id: str) -> str:
    """Save intermediate result for debugging."""
    filename = f"{run_id}_{step_name}.png"
    path = os.path.join(INTERMEDIATE_DIR, filename)
    with open(path, "wb") as f:
        f.write(image_bytes)
    logger.info(f"Saved intermediate: {path}")
    return path


async def run_localize_pipeline(
    image_bytes: bytes,
    filename: str,
    request: LocalizePipelineRequest,
    save_intermediates: bool = True,
) -> tuple[bytes, LocalizePipelineResponse]:
    """Run the full 3-step localization pipeline.

    Args:
        image_bytes: Raw input image bytes.
        filename: Original filename.
        request: Pipeline configuration with objects, context, texts.
        save_intermediates: Whether to save intermediate results.

    Returns:
        Tuple of (final_image_bytes, pipeline_response).
    """
    pipeline_start = time.time()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(filename)[0]
    run_id = f"{base_name}_{run_id}"

    steps: list[StepResult] = []
    current_bytes = image_bytes

    # Save original for reference
    if save_intermediates:
        _save_intermediate(current_bytes, "0_original", run_id)

    # ──────────────────────────────────────────────────────────────────────
    # Context Transformation (Background First)
    # ──────────────────────────────────────────────────────────────────────
    step_start = time.time()
    try:
        if request.background:
            current_bytes = await run_context_transformation(
                image_bytes=current_bytes,
                filename=filename,
                context=request.background,
                seed=(request.seed + 1000) if request.seed else None,
            )
            step_duration = time.time() - step_start
            steps.append(StepResult(
                step="context_transformation",
                status="success",
                message=f"Context transformed to '{request.background.scene_type}'.",
                duration_seconds=round(step_duration, 2),
            ))
            if save_intermediates:
                _save_intermediate(current_bytes, "after_context", run_id)
        else:
            steps.append(StepResult(
                step="context_transformation",
                status="skipped",
                message="No context transformation requested.",
                duration_seconds=0.0,
            ))
    except Exception as e:
        step_duration = time.time() - step_start
        logger.error(f"Context transformation failed: {e}", exc_info=True)
        steps.append(StepResult(
            step="context_transformation",
            status="error",
            message=str(e),
            duration_seconds=round(step_duration, 2),
        ))

    # ──────────────────────────────────────────────────────────────────────
    # Object Replacement (Foreground Second)
    # ──────────────────────────────────────────────────────────────────────
    step_start = time.time()
    try:
        if request.object_replacements:
            current_bytes = await run_object_replacement(
                image_bytes=current_bytes,
                filename=filename,
                object_replacements=request.object_replacements,
                seed=request.seed,
            )
            step_duration = time.time() - step_start
            steps.append(StepResult(
                step="object_replacement",
                status="success",
                message=f"Replaced {len(request.object_replacements)} object(s).",
                duration_seconds=round(step_duration, 2),
            ))
            if save_intermediates:
                _save_intermediate(current_bytes, "after_objects", run_id)
        else:
            steps.append(StepResult(
                step="object_replacement",
                status="skipped",
                message="No objects to replace.",
                duration_seconds=0.0,
            ))
    except Exception as e:
        step_duration = time.time() - step_start
        logger.error(f"Object replacement failed: {e}", exc_info=True)
        steps.append(StepResult(
            step="object_replacement",
            status="error",
            message=str(e),
            duration_seconds=round(step_duration, 2),
        ))

    # ──────────────────────────────────────────────────────────────────────
    # Text Replacement
    # ──────────────────────────────────────────────────────────────────────
    step_start = time.time()
    try:
        if request.texts:
            current_bytes = await run_text_replacement(
                image_bytes=current_bytes,
                texts=request.texts,
            )
            step_duration = time.time() - step_start
            steps.append(StepResult(
                step="text_replacement",
                status="success",
                message=f"Replaced {len(request.texts)} text region(s).",
                duration_seconds=round(step_duration, 2),
            ))
            if save_intermediates:
                _save_intermediate(current_bytes, "after_text", run_id)
        else:
            steps.append(StepResult(
                step="text_replacement",
                status="skipped",
                message="No text replacements.",
                duration_seconds=0.0,
            ))
    except Exception as e:
        step_duration = time.time() - step_start
        logger.error(f"Text replacement failed: {e}", exc_info=True)
        steps.append(StepResult(
            step="text_replacement",
            status="error",
            message=str(e),
            duration_seconds=round(step_duration, 2),
        ))

    # ──────────────────────────────────────────────────────────────────────
    # Save final output
    # ──────────────────────────────────────────────────────────────────────
    output_filename = f"{run_id}_final.png"
    output_path = os.path.join(OUTPUTS_DIR, output_filename)
    with open(output_path, "wb") as f:
        f.write(current_bytes)

    total_duration = round(time.time() - pipeline_start, 2)

    # Determine overall status
    statuses = [s.status for s in steps]
    if all(s in ("success", "skipped") for s in statuses):
        overall_status = "success"
    elif any(s == "success" for s in statuses):
        overall_status = "partial"
    else:
        overall_status = "error"

    response = LocalizePipelineResponse(
        status=overall_status,
        steps=steps,
        output_path=output_path,
        total_duration_seconds=total_duration,
    )

    logger.info(
        f"Pipeline completed: {overall_status} | "
        f"Total: {total_duration}s | Output: {output_path}"
    )

    return current_bytes, response
