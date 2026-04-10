"""
Pydantic models for Phase 2: Constrained Translation & Feedback Loop.

Defines data schemas for semantic chunks, translation results,
revision feedback, and the verified text pack output.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WarningLevel(str, Enum):
    """Warning severity levels for translation quality.

    Attributes:
        NONE: Translation passed review.
        WARNING: Translation failed review after max retries.
    """

    NONE = "none"
    WARNING = "warning"


class TranslatedBlock(BaseModel):
    """A text block with its translation result.

    Args:
        original_content: Source language text.
        translated_content: Target language translated text.
        bbox: Bounding box [x0, y0, x1, y1] from the original PDF.
        font: Original font family name.
        size: Original font size in points.
        color: Original font color as RGB packed integer.
        flags: Original font style flags.
        editability_tag: Permission level inherited from Phase 1.
        score: Reviser quality score (1-10).
        warning: Warning level if translation quality is insufficient.
        revision_reason: Reason from reviser if score < 8.
    """

    original_content: str = Field(..., description="Source language text")
    translated_content: str = Field(..., description="Translated target text")
    bbox: list[float] = Field(
        ..., description="Bounding box [x0, y0, x1, y1] from original PDF"
    )
    font: str = Field(default="", description="Original font family name")
    size: float = Field(default=0.0, description="Original font size in points")
    color: int = Field(default=0, description="Original font color as RGB integer")
    flags: int = Field(default=0, description="Original font style flags")
    editability_tag: str = Field(
        default="editable", description="Permission level from Phase 1"
    )
    score: float = Field(default=0.0, description="Reviser quality score (1-10)")
    warning: WarningLevel = Field(
        default=WarningLevel.NONE, description="Warning level"
    )
    revision_reason: str = Field(
        default="", description="Reason from reviser if score < 8"
    )


class SourceTextBlock(BaseModel):
    """A text block received from Phase 1 Standardized Pack.

    Args:
        content: Raw text content.
        bbox: Bounding box [x0, y0, x1, y1].
        font: Font family name.
        size: Font size in points.
        color: Font color integer.
        flags: Font style flags.
        editability_tag: Permission level.
    """

    content: str = Field(..., description="Raw text content")
    bbox: list[float] = Field(..., description="Bounding box [x0, y0, x1, y1]")
    font: str = Field(default="", description="Font family name")
    size: float = Field(default=0.0, description="Font size in points")
    color: int = Field(default=0, description="Font color integer")
    flags: int = Field(default=0, description="Font style flags")
    editability_tag: str = Field(default="editable", description="Permission level")


class SemanticChunk(BaseModel):
    """A group of text blocks chunked together for translation.

    Args:
        chunk_id: Unique identifier for this chunk.
        page_range: Range of page IDs included in this chunk.
        text_blocks: List of source text blocks in this chunk.
    """

    chunk_id: int = Field(..., description="Unique chunk identifier")
    page_range: list[int] = Field(
        ..., description="Page IDs included in this chunk"
    )
    text_blocks: list[SourceTextBlock] = Field(
        ..., description="Source text blocks in this chunk"
    )


class RevisionResult(BaseModel):
    """Result from the Reviser Agent's evaluation.

    Args:
        score: Quality score from 1 to 10.
        reason: Explanation for the score, especially if score < 8.
    """

    score: float = Field(..., description="Quality score from 1 to 10")
    reason: str = Field(default="", description="Explanation for the score")


class VerifiedTextPack(BaseModel):
    """Output pack containing verified translations for a chunk.

    Args:
        chunk_id: The chunk identifier.
        translated_blocks: List of translated blocks with scores.
        warnings: List of block indices that received warning tags.
    """

    chunk_id: int = Field(..., description="Chunk identifier")
    translated_blocks: list[TranslatedBlock] = Field(
        ..., description="Translated blocks with quality scores"
    )
    warnings: list[int] = Field(
        default_factory=list,
        description="Indices of blocks with warning tags",
    )


class TranslateRequest(BaseModel):
    """Request body for triggering translation.
    
    Args:
        phase1_base_url: Base URL of the Phase 1 API.
        gemini_api_key: API key for Gemini LLM. If not provided,
            falls back to GEMINI_API_KEY environment variable.
    """
    
    phase1_base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL of Phase 1 API",
    )
    gemini_api_key: Optional[str] = Field(
        default=None, description="Gemini API key (optional, uses env var fallback)"
    )
