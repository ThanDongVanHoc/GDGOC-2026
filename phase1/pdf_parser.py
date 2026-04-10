"""
Task #p1.2: Structural Parsing — PDF text and image extraction.

Uses PyMuPDF (fitz) to extract text blocks and image blocks
from each page of a PDF file, including spatial coordinates,
font metadata, and bounding box information.
"""

import fitz  # PyMuPDF

from phase1.models import ImageBlock, PageLayout, TextBlock


def extract_text_blocks_from_page(page_dict: dict) -> list[TextBlock]:
    """Extracts text blocks with spatial coordinates from a parsed PDF page dict.

    Iterates through all block → line → span elements in the PyMuPDF
    page dictionary to collect text content, bounding boxes, and font metadata.

    Args:
        page_dict: Dictionary from ``page.get_text("dict")`` containing
            blocks, lines, and spans with text and positional data.

    Returns:
        list[TextBlock]: A list of TextBlock objects, each containing
            content, bbox coordinates, font name, size, color, and flags.
    """
    text_blocks: list[TextBlock] = []

    for block in page_dict.get("blocks", []):
        # Only process text blocks (type 0), skip image blocks (type 1)
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                content = span.get("text", "").strip()
                if not content:
                    continue

                text_blocks.append(
                    TextBlock(
                        content=content,
                        bbox=list(span.get("bbox", [0, 0, 0, 0])),
                        font=span.get("font", ""),
                        size=span.get("size", 0.0),
                        color=span.get("color", 0),
                        flags=span.get("flags", 0),
                    )
                )

    return text_blocks


def extract_image_blocks_from_page(page_dict: dict) -> list[ImageBlock]:
    """Extracts image blocks with bounding boxes from a parsed PDF page dict.

    Identifies blocks of type 1 (image) in the PyMuPDF page dictionary
    and records their bounding box coordinates.

    Args:
        page_dict: Dictionary from ``page.get_text("dict")`` containing
            blocks with type and positional data.

    Returns:
        list[ImageBlock]: A list of ImageBlock objects, each containing
            the bounding box of an image region on the page.
    """
    image_blocks: list[ImageBlock] = []

    for block in page_dict.get("blocks", []):
        # Only process image blocks (type 1)
        if block.get("type") != 1:
            continue

        image_blocks.append(
            ImageBlock(bbox=list(block.get("bbox", [0, 0, 0, 0])))
        )

    return image_blocks


def parse_pdf(pdf_path: str) -> list[PageLayout]:
    """Parses a PDF file and extracts structural layout for all pages.

    Opens the PDF with PyMuPDF, iterates through every page, and
    extracts text blocks (content + bbox + font metadata) and image
    blocks (bbox) into a structured PageLayout per page.

    Args:
        pdf_path: Absolute or relative file path to the PDF to parse.

    Returns:
        list[PageLayout]: A list of PageLayout objects, one per page,
            each containing the page dimensions, text blocks, and image blocks.

    Raises:
        FileNotFoundError: If the specified PDF file does not exist.
        fitz.FileDataError: If the file is not a valid PDF.
    """
    doc = fitz.open(pdf_path)
    pages: list[PageLayout] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_dict = page.get_text("dict")

        text_blocks = extract_text_blocks_from_page(page_dict)
        image_blocks = extract_image_blocks_from_page(page_dict)

        pages.append(
            PageLayout(
                page_id=page_index + 1,
                width=page_dict.get("width", page.rect.width),
                height=page_dict.get("height", page.rect.height),
                text_blocks=text_blocks,
                image_blocks=image_blocks,
            )
        )

    doc.close()
    return pages
