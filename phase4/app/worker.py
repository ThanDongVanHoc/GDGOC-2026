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


import logging

async def run(payload: dict) -> dict:
    """
    Main entry point for Phase 4 processing based on Orchestrator payload.
    """
    output_phase_3 = payload.get("output_phase_3", {})
    images_tasks = output_phase_3.get("Images", [])
    
    # ── Orchestrator provides these:
    source_pdf_path = payload.get("source_pdf_path", "")
    source_pdf_url = payload.get("source_pdf_url", "")
    
    results = []
    
    if not images_tasks:
        logging.info("[Phase4] No Images in payload. Returning empty results.")
        return {"status": "success", "results": []}
        
    # ── 1. Smart Fallback for the PDF Source ─────────────────────
    # If the local path does not exist (e.g. running on local machine testing Azure data),
    # fetch the PDF via the url!
    pdf_local_path = source_pdf_path
    if not os.path.exists(pdf_local_path):
        logging.warning(f"[Phase4] Local PDF not found at {pdf_local_path}, falling back to remote url: {source_pdf_url}")
        
        download_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(download_dir, exist_ok=True)
        pdf_name = os.path.basename(pdf_local_path) if pdf_local_path else f"{uuid.uuid4().hex}.pdf"
        pdf_fallback_path = os.path.join(download_dir, pdf_name)
        
        try:
            download_if_needed(pdf_fallback_path, source_pdf_url)
            pdf_local_path = pdf_fallback_path
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to acquire PDF: {str(e)}"
            }

    # ── 2. Open Document and Process Tasks ────────────────────────
    import fitz
    
    try:
        doc = fitz.open(pdf_local_path)
    except Exception as e:
        return {"status": "error", "message": f"Failed to open PDF: {str(e)}"}
        
    for task_pair in images_tasks:
        if not isinstance(task_pair, list) or len(task_pair) < 2:
            continue
            
        meta_dict = task_pair[0]
        replacements_dict = task_pair[1]
        
        page_id = meta_dict.get("page_id", 1)
        bbox = meta_dict.get("bbox", [0, 0, 0, 0])
        image_index = meta_dict.get("image_index", 0)
        replacements_json = replacements_dict.get("replacements_json", {})
        
        # Crop PDF using bbox
        try:
            page_idx = max(0, page_id - 1)
            pdf_page = doc[page_idx]
            rect = fitz.Rect(bbox)
            pix = pdf_page.get_pixmap(clip=rect)
            image_bytes = pix.tobytes("png")
        except Exception as e:
            results.append({
                "page_id": page_id, "bbox": bbox, "image_index": image_index,
                "status": "error", "message": f"Failed to crop PDF bbox: {str(e)}"
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
        
        filename = f"image_pg{page_id}_{uuid.uuid4().hex[:8]}.png"
        
        try:
            result_bytes, pipeline_response = await run_localize_pipeline(
                image_bytes=image_bytes,
                filename=filename,
                request=request,
                save_intermediates=True
            )
            
            if pipeline_response.status == "error":
                results.append({
                    "page_id": page_id, "bbox": bbox, "image_index": image_index,
                    "status": "error", 
                    "message": f"Pipeline error: {[s.message for s in pipeline_response.steps if s.status == 'error']}"
                })
                continue
                
            output_path = pipeline_response.output_path
            if not output_path:
                download_dir = os.path.join(os.getcwd(), "downloads")
                os.makedirs(download_dir, exist_ok=True)
                output_path = os.path.join(download_dir, f"localized_{uuid.uuid4().hex[:8]}.png")
                with open(output_path, "wb") as f:
                    f.write(result_bytes)
                    
            with open(output_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
                
            results.append({
                "page_id": page_id,
                "bbox": bbox,
                "image_index": image_index,
                "image": img_b64,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "page_id": page_id, "bbox": bbox, "image_index": image_index,
                "image": None, 
                "status": "error", 
                "message": str(e)
            })
            
    doc.close()
            
    return {
        "status": "success",
        "results": results
    }
