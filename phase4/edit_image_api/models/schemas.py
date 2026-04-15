"""
Pydantic schemas for the 3-step localization pipeline.

Input format:
- objects: list of objects to replace (with bbox + replacement name)
- texts: list of text regions to replace (with bbox + new Vietnamese text)
- context: target culture/setting transformation instructions
"""

from typing import Optional

from pydantic import BaseModel, Field


# ── Step 1: Object Replacement ──────────────────────────────────────────────

class ObjectReplacement(BaseModel):
    """A single object to replace in the image."""
    bbox: list[int] = Field(
        ...,
        description="Bounding box [x1, y1, x2, y2] of the object to replace.",
        min_length=4,
        max_length=4,
    )
    original: str = Field(..., description="Name of the original object (e.g. 'hamburger').")
    replacement: str = Field(..., description="Name of the replacement object (e.g. 'bánh chưng').")


# ── Step 2: Context Transformation ──────────────────────────────────────────

class ContextTransformation(BaseModel):
    """Instructions for transforming the scene context/background."""
    target_culture: str = Field(
        default="Vietnamese",
        description="Target culture for localization.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional extra description for context transformation "
                    "(e.g. 'rural Vietnamese village with rice paddies').",
    )
    strength: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How strongly to transform the context. "
                    "0.0 = no change, 1.0 = maximum change.",
    )


# ── Step 3: Text Replacement ────────────────────────────────────────────────

class TextReplacement(BaseModel):
    """A single text region to replace."""
    bbox: list[int] = Field(
        ...,
        description="Bounding box [x1, y1, x2, y2] of the text to replace.",
        min_length=4,
        max_length=4,
    )
    original_text: str = Field(..., description="Original text content.")
    new_text: str = Field(..., description="Replacement Vietnamese text.")
    font_size: Optional[int] = Field(
        default=None,
        description="Font size override. If None, auto-detected from bbox height.",
    )
    font_color: Optional[str] = Field(
        default=None,
        description="Font color override as hex (e.g. '#FF0000'). "
                    "If None, auto-detected from original text region.",
    )


# ── Pipeline Request / Response ─────────────────────────────────────────────

class LocalizePipelineRequest(BaseModel):
    """Full request for the 3-step localization pipeline."""
    objects: list[ObjectReplacement] = Field(
        default_factory=list,
        description="Objects to replace. Empty list = skip step 1.",
    )
    context: Optional[ContextTransformation] = Field(
        default=None,
        description="Context transformation config. None = skip step 2.",
    )
    texts: list[TextReplacement] = Field(
        default_factory=list,
        description="Text regions to replace. Empty list = skip step 3.",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility.",
    )


class StepResult(BaseModel):
    """Result of a single pipeline step."""
    step: str
    status: str  # "success", "skipped", "error"
    message: str
    duration_seconds: float = 0.0


class LocalizePipelineResponse(BaseModel):
    """Response from the localization pipeline."""
    status: str  # "success", "partial", "error"
    steps: list[StepResult]
    output_path: Optional[str] = None
    total_duration_seconds: float = 0.0
