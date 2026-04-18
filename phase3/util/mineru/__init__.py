"""MinerU — PDF to Markdown/JSON conversion utility for OmniLocal.

Wraps the MinerU library (https://github.com/opendatalab/MinerU)
to convert PDF files into either raw Markdown or the #p1.2 Standardized
Pack JSON format consumed by downstream pipeline phases.

Quick start::

    from util.mineru import MinerUConverter

    converter = MinerUConverter(backend="pipeline")  # CPU-safe
    pack = converter.parse_pdf_to_standardized_pack("book.pdf")

    # Serialise to JSON matching #p1.2 schema
    print(pack.model_dump_json(indent=2))

    # Or get just the Markdown
    md = converter.parse_pdf_to_markdown("book.pdf")
"""

from util.mineru.converter import MinerUConverter, convert_pdf_to_standardized_pack
from util.mineru.models import DocumentPack, ImageBlock, PageLayout, TextBlock

__all__ = [
    "MinerUConverter",
    "convert_pdf_to_standardized_pack",
    "DocumentPack",
    "PageLayout",
    "TextBlock",
    "ImageBlock",
]
