"""
OmniLocal — Phase 4 Worker: Visual Reconstruction & Compositing.

Your tasks:
    1. Track A: Generate masks (OpenCV) → Inpaint scenes (Stable Diffusion + ControlNet).
    2. Track B: Compute text layout (Knuth-Plass) → Handle overflow (LLM summarize).
    3. Track C: Composite image + text → Apply publishing compliance rules.
    4. Output print-ready PDF (CMYK, 300 DPI, 5mm margin, K-Black, font embedded).
    5. Handle qa_feedback if this is a QA-triggered re-run.

    Track A and Track B can run in parallel — your decision.
"""

import os
import uuid
import base64

from pipeline.localize_pipeline import run_localize_pipeline
from models.schemas import LocalizePipelineRequest, BackgroundData
from app.utils import download_if_needed


async def run(payload: dict) -> dict:
    """
    Main entry point for Phase 4 processing.

    Args:
        payload: Contains image_path and replacements_json
    """
    tasks = payload.get("tasks", [])
    results = []
    
    for task in tasks:
        # Expected structure: {"image_path": "...", "image_url": "...", "replacements_json": {...}}
        if not isinstance(task, dict):
            continue
            
        image_url = task.get("image_url")
        replacements_json = task.get("replacements_json", {})
        
        # Determine a local path for the downloaded image
        # Using a 'downloads' folder or current directory as fallback
        download_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(download_dir, exist_ok=True)
        
        # Generate a unique filename if we don't have a path
        image_path = os.path.join(download_dir, f"input_{uuid.uuid4().hex[:8]}.png")
        
        # Download/read image bytes
        try:
            image_bytes = download_if_needed(image_path, image_url)
        except Exception as e:
            results.append({
                "original_image": image_path,
                "status": "error",
                "message": f"Failed to obtain image: {str(e)}"
            })
            continue

        background_dict = replacements_json.get("Background", {})
        object_replacements = replacements_json.get("Object_Replacement", {})
        
        background = None
        if background_dict and "scene_type" in background_dict:
            background = BackgroundData(
                scene_type=background_dict["scene_type"],
                preserved_foreground=background_dict.get("preserved_foreground", []),
                modified_background_elements=background_dict.get("modified_background_elements", []),
                vietnamese_setting_suggestions=background_dict.get("vietnamese_setting_suggestions", []),
                constraints=background_dict.get("constraints", [])
            )
            
        request = LocalizePipelineRequest(
            background=background,
            object_replacements=object_replacements if object_replacements else {},
            texts=[],
            seed=None
        )
        
        filename = os.path.basename(image_path) if image_path else f"image_{uuid.uuid4().hex[:8]}.png"
        
        try:
            result_bytes, pipeline_response = await run_localize_pipeline(
                image_bytes=image_bytes,
                filename=filename,
                request=request,
                save_intermediates=True
            )
            
            if pipeline_response.status == "error":
                results.append({
                    "original_image": image_path, 
                    "status": "error", 
                    "message": f"Pipeline error: {[s.message for s in pipeline_response.steps if s.status == 'error']}"
                })
                continue
                
            output_path = pipeline_response.output_path
            if not output_path:
                # Use image_path's directory if it's local, otherwise use current dir
                base_dir = os.path.dirname(image_path) if image_path and os.path.isabs(image_path) else "."
                output_path = os.path.join(base_dir, f"localized_{uuid.uuid4().hex[:8]}.png")
                with open(output_path, "wb") as f:
                    f.write(result_bytes)
                    
            with open(output_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
                
            results.append({
                "image": img_b64,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "image": None, 
                "status": "error", 
                "message": str(e)
            })
            
    return {
        "status": "success",
        "results": results
    }
