"""
Pydantic models for Phase 1: Ingestion & Structural Parsing.

Defines the data schemas for text blocks, image blocks, page layouts,
global metadata constraints, and the standardized pack output.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EditabilityTag(str, Enum):
    """Editability permission levels for content blocks.

    Attributes:
        EDITABLE: Full edit rights (text + image).
        SEMI_EDITABLE: Text-only edits allowed, image locked.
        NON_EDITABLE: Fully locked, no modifications permitted.
    """

    EDITABLE = "editable"
    SEMI_EDITABLE = "semi-editable"
    NON_EDITABLE = "non-editable"


class TranslationFidelity(str, Enum):
    """Translation fidelity levels.

    Attributes:
        STRICT: No additions or removals allowed.
        EXPLANATORY: Small clarifying notes permitted, but no text changes.
    """

    STRICT = "Strict"
    EXPLANATORY = "Explanatory"


class SfxHandling(str, Enum):
    """Sound effect handling modes for graphic onomatopoeia.

    Attributes:
        IN_PANEL_SUBS: Faded subtitle next to original.
        FOOTNOTES: Footnote at page bottom.
        KEEP_ORIGINAL: Preserve as-is.
    """

    IN_PANEL_SUBS = "In_panel_subs"
    FOOTNOTES = "Footnotes"
    KEEP_ORIGINAL = "Keep_original"


class TextBlock(BaseModel):
    """A single text block extracted from a PDF page.

    Args:
        content: The raw text content of the block.
        bbox: Bounding box coordinates [x0, y0, x1, y1] in PDF points.
        font: Font family name.
        size: Font size in points.
        color: Font color as an integer (RGB packed).
        flags: Font style flags (bold, italic, etc.).
        editability_tag: Permission level for this block.
    """

    content: str = Field(..., description="Raw text content of the block")
    bbox: list[float] = Field(
        ..., description="Bounding box [x0, y0, x1, y1] in PDF points"
    )
    font: str = Field(default="", description="Font family name")
    size: float = Field(default=0.0, description="Font size in points")
    color: int = Field(default=0, description="Font color as RGB packed integer")
    flags: int = Field(default=0, description="Font style flags (bold, italic, etc.)")
    editability_tag: EditabilityTag = Field(
        default=EditabilityTag.EDITABLE,
        description="Permission level for this block",
    )


class ImageBlock(BaseModel):
    """A single image block extracted from a PDF page.

    Args:
        bbox: Bounding box coordinates [x0, y0, x1, y1] in PDF points.
        editability_tag: Permission level for this block.
    """

    bbox: list[float] = Field(
        ..., description="Bounding box [x0, y0, x1, y1] in PDF points"
    )
    editability_tag: EditabilityTag = Field(
        default=EditabilityTag.NON_EDITABLE,
        description="Permission level for this block",
    )


class PageLayout(BaseModel):
    """Structural layout data for a single PDF page.

    Args:
        page_id: 1-indexed page number.
        width: Page width in PDF points.
        height: Page height in PDF points.
        text_blocks: List of text blocks on this page.
        image_blocks: List of image blocks on this page.
    """

    page_id: int = Field(..., description="1-indexed page number")
    width: float = Field(..., description="Page width in PDF points")
    height: float = Field(..., description="Page height in PDF points")
    text_blocks: list[TextBlock] = Field(
        default_factory=list, description="Text blocks on this page"
    )
    image_blocks: list[ImageBlock] = Field(
        default_factory=list, description="Image blocks on this page"
    )


class LegalParameters(BaseModel):
    """Legal constraint parameters based on Moral Rights.

    Args:
        license_status: Whether the translation is legally licensed.
        author_attribution: Required attribution string for the original author.
        integrity_protection: Whether integrity of original work must be preserved.
        adaptation_rights: Whether adaptation (transcreation) is permitted.
    """

    license_status: bool = Field(
        default=True, description="Legal license status for translation"
    )
    author_attribution: str = Field(
        default="", description="Required author attribution text"
    )
    integrity_protection: bool = Field(
        default=True, description="Protect integrity of original work"
    )
    adaptation_rights: bool = Field(
        default=False, description="Allow adaptation beyond translation"
    )


class ContentParameters(BaseModel):
    """Content control parameters for translation fidelity.

    Args:
        translation_fidelity: Level of translation fidelity (Strict or Explanatory).
        plot_alteration: Whether plot changes are allowed.
        cultural_localization: Whether cultural adaptation is allowed.
    """

    translation_fidelity: TranslationFidelity = Field(
        default=TranslationFidelity.STRICT,
        description="Translation fidelity level",
    )
    plot_alteration: bool = Field(
        default=False, description="Allow plot alterations"
    )
    cultural_localization: bool = Field(
        default=False, description="Allow cultural localization"
    )


class IpBrandParameters(BaseModel):
    """IP and brand protection parameters.

    Args:
        preserve_main_names: Keep original character names (transliterate only).
        no_retouching: Prohibit redrawing or retouching original images.
        lock_character_color: Lock character colors to original spec.
        never_change_rules: List of immutable visual characteristics.
        protected_names: List of proper names that must not be translated.
    """

    preserve_main_names: bool = Field(
        default=True, description="Preserve original character names"
    )
    no_retouching: bool = Field(
        default=True, description="Prohibit image retouching"
    )
    lock_character_color: bool = Field(
        default=True, description="Lock character colors"
    )
    never_change_rules: list[str] = Field(
        default_factory=list,
        description="Immutable visual rules",
    )
    protected_names: list[str] = Field(
        default_factory=list,
        description="Names that must not be translated",
    )


class EditorialParameters(BaseModel):
    """Editorial constraint parameters for style and workflow.

    Args:
        source_language: Source language code (e.g., 'EN').
        target_language: Target language code (e.g., 'VI').
        style_register: Writing style descriptor for audience.
        target_age_tone: Target age for tone calibration.
        glossary_strict_mode: Enforce style guide and glossary 100%.
        sfx_handling: How to handle graphic sound effects.
        allow_bg_edit: Whether background editing is permitted.
        satisfaction_clause: Whether licensor has final veto rights.
    """

    source_language: str = Field(default="EN", description="Source language code")
    target_language: str = Field(default="VI", description="Target language code")
    style_register: str = Field(
        default="", description="Writing style for target audience"
    )
    target_age_tone: int = Field(
        default=8, description="Target age for tone calibration"
    )
    glossary_strict_mode: bool = Field(
        default=False, description="Enforce glossary strictly"
    )
    sfx_handling: SfxHandling = Field(
        default=SfxHandling.IN_PANEL_SUBS,
        description="Sound effect handling mode",
    )
    allow_bg_edit: bool = Field(
        default=False, description="Allow background editing"
    )
    satisfaction_clause: bool = Field(
        default=True, description="Licensor has final veto rights"
    )


class GlobalMetadata(BaseModel):
    """Complete global metadata constraints for the localization project.

    Args:
        legal_parameters: Legal constraints based on Moral Rights.
        content_parameters: Content fidelity controls.
        ip_brand_parameters: IP and brand protection rules.
        editorial_parameters: Editorial style and workflow constraints.
    """

    legal_parameters: LegalParameters = Field(default_factory=LegalParameters)
    content_parameters: ContentParameters = Field(default_factory=ContentParameters)
    ip_brand_parameters: IpBrandParameters = Field(default_factory=IpBrandParameters)
    editorial_parameters: EditorialParameters = Field(
        default_factory=EditorialParameters
    )


class StandardizedPack(BaseModel):
    """Combined output pack for Phase 1 handoff.

    Args:
        global_metadata: Project-wide constraints.
        pages: List of parsed page layouts with editability tags.
    """

    global_metadata: GlobalMetadata = Field(
        ..., description="Project-wide constraints"
    )
    pages: list[PageLayout] = Field(
        ..., description="Parsed page layouts with editability tags"
    )


class IngestBriefRequest(BaseModel):
    """Request payload for extracting metadata from a raw brief."""
    raw_brief_text: str = Field(
        ...,
        description="The raw unstructured text (e.g., email or project brief) explaining constraint settings.",
    )
    gemini_api_key: str | None = Field(
        default=None,
        description="Optional API key. If not passed, defaults to GEMINI_API_KEY env var.",
    )
