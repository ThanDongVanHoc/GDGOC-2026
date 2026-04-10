"""
OmniLocal Orchestrator — Pydantic Schemas for Webhook payloads.
"""

from typing import Any

from pydantic import BaseModel, Field


class WebhookPayload(BaseModel):
    """Payload sent by a Phase Worker when processing is complete."""

    thread_id: str = Field(
        ..., description="Pipeline run ID — must match the original dispatch."
    )
    result: dict[str, Any] = Field(
        ..., description="Phase output data to merge into OmniLocalState."
    )
    error: str | None = Field(
        default=None, description="Error message if processing failed."
    )
