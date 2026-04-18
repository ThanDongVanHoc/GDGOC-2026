"""Pydantic models for MinerU output → #p1.2 Standardized Pack.

Mirrors the JSON schema defined in Phase1_Ingestion_StructuralParsing.md
(Task #p1.2) so that downstream phases can consume a validated, typed
representation of every page's spatial layout.

Target schema example:
    {
      "page_id": 1,
      "width": 595.0,
      "height": 842.0,
      "text_blocks": [
        { "content": "Once upon a time...", "bbox": [72, 100, 523, 130] }
      ],
      "image_blocks": [
        { "bbox": [50, 200, 545, 600] }
      ]
    }
"""

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    """A contiguous run of text with its bounding box on the page.

    Attributes:
        content: The extracted text content of this block.
        bbox: Spatial coordinates as [x0, y0, x1, y1] in PDF points.
    """

    content: str
    bbox: list[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box [x0, y0, x1, y1] in PDF points.",
    )


class ImageBlock(BaseModel):
    """An image region identified on the page.

    Attributes:
        bbox: Spatial coordinates as [x0, y0, x1, y1] in PDF points.
        image_path: Optional path to the extracted image file on disk.
    """

    bbox: list[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box [x0, y0, x1, y1] in PDF points.",
    )
    image_path: str | None = Field(
        default=None,
        description="Relative path to the extracted image file, if available.",
    )


class PageLayout(BaseModel):
    """Complete spatial layout of a single page — the #p1.2 output unit.

    Attributes:
        page_id: 1-indexed page number.
        width: Page width in PDF points.
        height: Page height in PDF points.
        text_blocks: All text regions detected on this page.
        image_blocks: All image regions detected on this page.
    """

    page_id: int = Field(..., ge=1, description="1-indexed page number.")
    width: float = Field(..., gt=0, description="Page width in PDF points.")
    height: float = Field(..., gt=0, description="Page height in PDF points.")
    text_blocks: list[TextBlock] = Field(default_factory=list)
    image_blocks: list[ImageBlock] = Field(default_factory=list)


class DocumentPack(BaseModel):
    """Full document converted to the Standardized Pack format.

    Wraps all page layouts plus optional document-level metadata so
    the entire book can be serialised / deserialised in one shot.

    Attributes:
        source_file: Original PDF filename that was parsed.
        total_pages: Number of pages in the document.
        pages: Ordered list of per-page layout data.
        markdown_content: Full Markdown text produced by MinerU (optional).
    """

    source_file: str = Field(..., description="Original PDF filename.")
    total_pages: int = Field(..., ge=0)
    pages: list[PageLayout] = Field(default_factory=list)
    markdown_content: str | None = Field(
        default=None,
        description="Full Markdown output from MinerU, when available.",
    )
