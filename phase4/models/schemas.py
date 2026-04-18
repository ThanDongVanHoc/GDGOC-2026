"""
Pydantic schemas for the 3-step localization pipeline.

Input format:
- objects: list of objects to replace (with bbox + replacement name)
- texts: list of text regions to replace (with bbox + new Vietnamese text)
- context: target culture/setting transformation instructions
"""

from typing import Optional

from pydantic import BaseModel, Field


# ── Step 1 & 2: Replacements JSON Schema ──────────────────────────────────────

class BackgroundData(BaseModel):
    """Instructions for transforming the scene context/background."""
    scene_type: str = Field(..., description="The target scene type (e.g. indoor dining room).")
    preserved_foreground: list[str] = Field(default_factory=list, description="Elements to preserve.")
    modified_background_elements: list[str] = Field(default_factory=list, description="Elements to modify.")
    vietnamese_setting_suggestions: list[str] = Field(default_factory=list, description="Vietnamese localization suggestions.")
    constraints: list[str] = Field(default_factory=list, description="Hard generation constraints.")


class ReplacementsJson(BaseModel):
    Background: Optional[BackgroundData] = None
    Object_Replacement: dict[str, str] = Field(default_factory=dict)



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
    background: Optional[BackgroundData] = Field(
        default=None,
        description="Background transformation config. None = skip context transformation.",
    )
    object_replacements: dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping original object names to replacements. Empty = skip.",
    )
    texts: list[TextReplacement] = Field(
        default_factory=list,
        description="Text regions to replace. Empty list = skip text replacement.",
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
