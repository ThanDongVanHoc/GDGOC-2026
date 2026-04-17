"""
OmniLocal Orchestrator — FastAPI Application.

Entry point for the Orchestrator service.
Serves the pipeline API + webhook receiver + static frontend files.
"""

import asyncio
import base64
import os
import uuid

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.schemas.pipeline import PipelineStartRequest, DemoStartRequest, PipelineStatusResponse
from app.state import OmniLocalState
from app.webhook import router as webhook_router
from app.graph import build_graph, build_demo_graph
from app.db import execute_graph

app = FastAPI(
    title="OmniLocal Orchestrator",
    description="LangGraph-based pipeline orchestrator for cross-cultural book localization.",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register webhook routes
app.include_router(webhook_router)

# Expose uploaded PDFs for remote workers
app.mount("/uploads", StaticFiles(directory="data/uploads"), name="uploads")

# In-memory pipeline store (for quick lookups alongside SQLite state)
_pipelines: dict[str, OmniLocalState] = {}


@app.get("/")
async def root() -> dict:
    """Health check endpoint."""
    return {"service": "OmniLocal Orchestrator", "status": "running"}


@app.post("/api/v1/pipeline/demo", response_model=PipelineStatusResponse)
async def start_demo_pipeline(request: DemoStartRequest) -> PipelineStatusResponse:
    """
    Start a Phase 0 demo flow using a camera picture.
    """
    thread_id = str(uuid.uuid4())
    
    # Extract & Save base64 image
    b64_data = request.base64_image.split(",")[1] if "," in request.base64_image else request.base64_image
    upload_dir = os.path.abspath("data/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    img_path = os.path.join(upload_dir, f"{thread_id}.jpg")
    
    with open(img_path, "wb") as f:
        f.write(base64.b64decode(b64_data))

    initial_state: OmniLocalState = {
        "thread_id": thread_id,
        "current_phase": 0,
        "status": "PROCESSING",
        "pipeline_iteration": 0,
        "source_pdf_path": "",
        "brief_path": "",
        "global_metadata": {},
        "camera_image_path": img_path,
        "phase0_results": None,
        "output_phase_1": None,
        "output_phase_2": None,
        "output_phase_3": None,
        "output_phase_4": None,
        "qa_status": "",
        "qa_feedback": None,
        "final_pdf_path": "",
        "dispatch_info": {},
    }

    _pipelines[thread_id] = initial_state

    # Invoke Demo graph asynchronously mapping safe async db checkpoints
    asyncio.create_task(
        execute_graph(build_demo_graph, initial_state, thread_id)
    )

    return PipelineStatusResponse(
        thread_id=thread_id,
        current_phase=0,
        status="PROCESSING",
    )


@app.post("/api/v1/pipeline/start", response_model=PipelineStatusResponse)
async def start_pipeline(request: PipelineStartRequest) -> PipelineStatusResponse:
    """
    Start a new localization pipeline.

    Creates a new pipeline run and begins Phase 1 execution.

    Args:
        request: Contains source_pdf_path and brief_path.

    Returns:
        Pipeline status with thread_id for tracking.
    """
    thread_id = str(uuid.uuid4())

    initial_state: OmniLocalState = {
        "thread_id": thread_id,
        "current_phase": 0,
        "status": "IDLE",
        "pipeline_iteration": 0,
        "source_pdf_path": request.source_pdf_path,
        "brief_path": request.brief_path,
        "global_metadata": {},
        "camera_image_path": "",
        "phase0_results": None,
        "output_phase_1": None,
        "output_phase_2": None,
        "output_phase_3": None,
        "output_phase_4": None,
        "qa_status": "",
        "qa_feedback": None,
        "final_pdf_path": "",
        "dispatch_info": {},
    }

    _pipelines[thread_id] = initial_state

    # Invoke Main graph asynchronously with Checkpointer
    asyncio.create_task(
        execute_graph(build_graph, initial_state, thread_id)
    )

    return PipelineStatusResponse(
        thread_id=thread_id,
        current_phase=0,
        status="IDLE",
    )


@app.post("/api/v1/pipeline/upload-and-start", response_model=PipelineStatusResponse)
async def upload_and_start(
    file: UploadFile = File(...),
    brief: str = Form(...)
) -> PipelineStatusResponse:
    """
    Start a new pipeline using a standard multipart form upload.
    This works perfectly with web browsers.
    """
    thread_id = str(uuid.uuid4())
    upload_dir = os.path.abspath("data/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    pdf_path = os.path.join(upload_dir, f"{thread_id}.pdf")
    brief_path = os.path.join(upload_dir, f"{thread_id}_brief.txt")
    
    content = await file.read()
    with open(pdf_path, "wb") as f:
        f.write(content)
        
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(brief)
        
    initial_state: OmniLocalState = {
        "thread_id": thread_id,
        "current_phase": 0,
        "status": "IDLE",
        "pipeline_iteration": 0,
        "source_pdf_path": pdf_path,
        "brief_path": brief_path,
        "global_metadata": {},
        "camera_image_path": "",
        "phase0_results": None,
        "output_phase_1": None,
        "output_phase_2": None,
        "output_phase_3": None,
        "output_phase_4": None,
        "qa_status": "",
        "qa_feedback": None,
        "final_pdf_path": "",
        "dispatch_info": {},
    }

    _pipelines[thread_id] = initial_state

    # Invoke Main graph asynchronously with Checkpointer
    asyncio.create_task(
        execute_graph(build_graph, initial_state, thread_id)
    )

    return PipelineStatusResponse(
        thread_id=thread_id,
        current_phase=0,
        status="IDLE",
    )


@app.get("/api/v1/pipeline/{thread_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(thread_id: str) -> PipelineStatusResponse:
    """
    Get the current status of a pipeline run.

    Args:
        thread_id: The unique pipeline run ID.

    Returns:
        Current pipeline status.
    """
    state = _pipelines.get(thread_id)
    if not state:
        return PipelineStatusResponse(
            thread_id=thread_id, current_phase=0, status="NOT_FOUND"
        )

    return PipelineStatusResponse(
        thread_id=state["thread_id"],
        current_phase=state["current_phase"],
        status=state["status"],
        pipeline_iteration=state.get("pipeline_iteration", 0),
        qa_status=state.get("qa_status") or None,
        final_pdf_path=state.get("final_pdf_path") or None,
        dispatch_info=state.get("dispatch_info", {}),
    )
