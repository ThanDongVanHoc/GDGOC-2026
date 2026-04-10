"""
Task #p1.4: API Handoff — FastAPI application for Phase 1.

Exposes REST endpoints to upload PDFs, retrieve task graphs
(Standardized Packs), and access global metadata constraints.
"""

import json
import os
import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from phase1.editability_tagger import tag_all_pages
from phase1.metadata_extractor import extract_metadata_from_brief
from phase1.models import GlobalMetadata, IngestBriefRequest, PageLayout, StandardizedPack
from phase1.pdf_parser import parse_pdf

app = FastAPI(
    title="OmniLocal Phase 1 — Ingestion & Structural Parsing",
    description=(
        "Converts raw PDF assets into a standardized JSON pack with "
        "layout coordinates, font metadata, and editability tags."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for parsed data
_parsed_pages: list[PageLayout] = []
_global_metadata: GlobalMetadata | None = None

UPLOAD_DIR = Path("uploads")
METADATA_PATH = Path(__file__).parent / "global_metadata.json"


def _load_global_metadata() -> GlobalMetadata:
    """Loads global metadata from the default JSON file.

    Returns:
        GlobalMetadata: Parsed and validated global metadata object.

    Raises:
        FileNotFoundError: If global_metadata.json is missing.
    """
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return GlobalMetadata(**data)


@app.on_event("startup")
async def startup_event() -> None:
    """Initializes the application on startup.

    Loads global metadata and ensures the upload directory exists.
    """
    global _global_metadata
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _global_metadata = _load_global_metadata()


@app.post("/api/v1/extract-metadata", response_model=GlobalMetadata)
async def extract_metadata(request: IngestBriefRequest) -> GlobalMetadata:
    """Extracts structured GlobalMetadata from a raw project brief string.

    Uses Gemini API to interpret the unstructured text and maps it into
    our predefined GlobalMetadata JSON schema. The output replaces the
    current global_metadata.json and acts as constraints for the Phase 1 run.

    Args:
        request: Payload containing raw brief text and optional API key.

    Returns:
        GlobalMetadata: The structured metadata object.

    Raises:
        HTTPException: 400 if Gemini API key is missing.
        HTTPException: 500 if the LLM extraction fails.
    """
    global _global_metadata

    api_key = request.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key is required. Provide via request body or GEMINI_API_KEY.",
        )

    try:
        # 1. Call metadata_extractor
        extracted_meta = extract_metadata_from_brief(
            raw_brief_text=request.raw_brief_text,
            api_key=api_key
        )

        # 2. Overwrite the file so POST /api/v1/upload uses it
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            f.write(extracted_meta.model_dump_json(indent=2))

        # 3. Update RAM
        _global_metadata = extracted_meta

        return extracted_meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metadata Extraction failed: {str(e)}")


@app.post("/api/v1/upload", response_model=StandardizedPack)
async def upload_pdf(file: UploadFile = File(...)) -> StandardizedPack:
    """Uploads a PDF file and processes it into a Standardized Pack.

    Saves the uploaded file, parses it with PyMuPDF, applies editability
    tags based on global metadata, and returns the full Standardized Pack.

    Args:
        file: The uploaded PDF file.

    Returns:
        StandardizedPack: Complete pack with global metadata and tagged pages.

    Raises:
        HTTPException: 400 if the file is not a PDF.
        HTTPException: 500 if parsing fails.
    """
    global _parsed_pages

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        pages = parse_pdf(str(file_path))
        _parsed_pages = tag_all_pages(pages, _global_metadata)

        return StandardizedPack(
            global_metadata=_global_metadata,
            pages=_parsed_pages,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {e}")


@app.get("/api/v1/task-graph/{page_id}", response_model=PageLayout)
async def get_task_graph_by_page(page_id: int) -> PageLayout:
    """Returns the Standardized Pack data for a specific page.

    Args:
        page_id: 1-indexed page number to retrieve.

    Returns:
        PageLayout: Layout data for the requested page.

    Raises:
        HTTPException: 404 if no PDF has been uploaded yet.
        HTTPException: 404 if the page_id is out of range.
    """
    if not _parsed_pages:
        raise HTTPException(
            status_code=404,
            detail="No PDF has been uploaded yet. Use POST /api/v1/upload first.",
        )

    for page in _parsed_pages:
        if page.page_id == page_id:
            return page

    raise HTTPException(
        status_code=404,
        detail=f"Page {page_id} not found. Available pages: 1-{len(_parsed_pages)}.",
    )


@app.get("/api/v1/task-graph", response_model=StandardizedPack)
async def get_full_task_graph() -> StandardizedPack:
    """Returns the full Standardized Pack for all pages.

    Returns:
        StandardizedPack: Complete pack with global metadata and all tagged pages.

    Raises:
        HTTPException: 404 if no PDF has been uploaded yet.
    """
    if not _parsed_pages:
        raise HTTPException(
            status_code=404,
            detail="No PDF has been uploaded yet. Use POST /api/v1/upload first.",
        )

    return StandardizedPack(
        global_metadata=_global_metadata,
        pages=_parsed_pages,
    )


@app.get("/api/v1/global-metadata", response_model=GlobalMetadata)
async def get_global_metadata() -> GlobalMetadata:
    """Returns the current global metadata constraints.

    Returns:
        GlobalMetadata: The loaded global metadata configuration.
    """
    return _global_metadata
