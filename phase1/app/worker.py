"""
OmniLocal — Phase 1 Worker: Ingestion & Structural Parsing.

This is where you implement all Phase 1 logic.
The Orchestrator does NOT see this file — it only calls main.py.

Your tasks:
    1. Parse project brief → extract global_metadata.
    2. Parse PDF (PyMuPDF) → extract text/image blocks with bbox.
    3. Tag editability for each block.
"""


async def run(payload: dict) -> dict:
    """
    Main entry point for Phase 1 processing.

    Args:
        payload: Contains source_pdf_path and brief_path.

    Returns:
        Dictionary with global_metadata and standardized_pack.
    """
    source_pdf_path = payload["source_pdf_path"]
    brief_path = payload["brief_path"]

    # TODO: Implement your logic here
    # Step 1: Parse brief → extract constraints
    global_metadata = _parse_brief(brief_path)

    # Step 2: Parse PDF → extract blocks with bbox
    standardized_pack = _parse_pdf(source_pdf_path)

    # Step 3: Tag editability
    standardized_pack = _tag_editability(standardized_pack, global_metadata)

    return {
        "global_metadata": global_metadata,
        "standardized_pack": standardized_pack,
    }


def _parse_brief(brief_path: str) -> dict:
    """Parse project brief and extract global metadata constraints."""
    # TODO: Implement — read DOCX/XLSX, extract constraints
    return {
        "source_language": "EN",
        "target_language": "VI",
        "style_register": "children_under_10",
        "allow_bg_edit": True,
        "lock_character_color": True,
        "protected_names": [],
        "max_drift_ratio": 0.15,
    }


def _parse_pdf(pdf_path: str) -> list[dict]:
    """Parse PDF with PyMuPDF and extract text/image blocks with bbox."""
    # TODO: Implement — use fitz (PyMuPDF) page.get_text("dict")
    return []


def _tag_editability(pack: list[dict], metadata: dict) -> list[dict]:
    """Assign editability tags to each block based on global metadata."""
    # TODO: Implement — tag each block as editable/semi-editable/non-editable
    return pack
