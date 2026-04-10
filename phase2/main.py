"""
Task #p2.5: API Handoff — FastAPI application for Phase 2.

Exposes REST endpoints to trigger translation, retrieve verified text
packs by chunk, and list all warning-tagged translations.
"""

import logging
import os
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from phase2.feedback_loop import process_all_chunks
from phase2.models import TranslateRequest, VerifiedTextPack
from phase2.semantic_chunker import create_chunks_from_standardized_pack

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OmniLocal Phase 2 — Constrained Translation & Feedback Loop",
    description=(
        "Translates text blocks from Phase 1 using Gemini 2.5 Pro with "
        "a Translator-Reviser feedback loop and circuit breaker."
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

# In-memory storage for translation results
_verified_packs: list[VerifiedTextPack] = []


@app.post("/api/v1/translate", response_model=list[VerifiedTextPack])
async def translate(request: TranslateRequest) -> list[VerifiedTextPack]:
    """Triggers the full translation pipeline.

    Fetches the Standardized Pack from Phase 1, creates semantic chunks,
    and runs each through the Translator-Reviser feedback loop.

    Args:
        request: Contains the Phase 1 base URL and optional Gemini API key.

    Returns:
        list[VerifiedTextPack]: List of verified text packs with translations.

    Raises:
        HTTPException: 500 if Phase 1 API is unreachable or translation fails.
    """
    global _verified_packs

    api_key = request.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Gemini API key is required. Provide via request body or GEMINI_API_KEY env var.",
        )

    # Fetch Standardized Pack from Phase 1
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{request.phase1_base_url}/api/v1/task-graph"
            )
            response.raise_for_status()
            standardized_pack = response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Standardized Pack from Phase 1: {e}",
        )

    # Create semantic chunks
    global_metadata = standardized_pack.get("global_metadata", {})
    chunks = create_chunks_from_standardized_pack(standardized_pack)

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No text blocks found in the Standardized Pack.",
        )

    logger.info("Created %d semantic chunks for translation", len(chunks))

    # Process all chunks through the feedback loop
    _verified_packs = process_all_chunks(
        chunks=chunks,
        global_metadata=global_metadata,
        api_key=api_key,
    )

    return _verified_packs


@app.get("/api/v1/verified-text/{chunk_id}", response_model=VerifiedTextPack)
async def get_verified_text(chunk_id: int) -> VerifiedTextPack:
    """Returns the Verified Text Pack for a specific chunk.

    Args:
        chunk_id: The unique identifier of the chunk.

    Returns:
        VerifiedTextPack: The verified translation data for the chunk.

    Raises:
        HTTPException: 404 if no translations exist or chunk not found.
    """
    if not _verified_packs:
        raise HTTPException(
            status_code=404,
            detail="No translations available. Use POST /api/v1/translate first.",
        )

    for pack in _verified_packs:
        if pack.chunk_id == chunk_id:
            return pack

    raise HTTPException(
        status_code=404,
        detail=f"Chunk {chunk_id} not found. Available: {[p.chunk_id for p in _verified_packs]}",
    )


@app.get("/api/v1/verified-text/warnings", response_model=list[VerifiedTextPack])
async def get_warnings() -> list[VerifiedTextPack]:
    """Returns all chunks that have warning tags.

    Returns:
        list[VerifiedTextPack]: List of verified packs containing warnings.

    Raises:
        HTTPException: 404 if no translations exist.
    """
    if not _verified_packs:
        raise HTTPException(
            status_code=404,
            detail="No translations available. Use POST /api/v1/translate first.",
        )

    return [pack for pack in _verified_packs if pack.warnings]
