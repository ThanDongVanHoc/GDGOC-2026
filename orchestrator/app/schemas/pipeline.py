"""
OmniLocal Orchestrator — Pydantic Schemas for Pipeline API.
"""

from pydantic import BaseModel, Field


class PipelineStartRequest(BaseModel):
    """Request body for starting a new pipeline run."""

    source_pdf_path: str = Field(
        ..., description="Path to the source PDF file."
    )
    brief_path: str = Field(
        ..., description="Path to the project brief (DOCX/XLSX)."
    )


class DemoStartRequest(BaseModel):
    """Request body for starting the Phase 0 Camera demo."""

    base64_image: str = Field(
        ..., description="Base64 encoded string of the captured camera image."
    )


class PipelineStatusResponse(BaseModel):
    """Response body for pipeline status queries."""

    thread_id: str
    current_phase: int
    status: str
    pipeline_iteration: int = 0
    qa_status: str | None = None
    final_pdf_path: str | None = None
