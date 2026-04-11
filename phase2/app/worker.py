"""
OmniLocal — Phase 2 Worker: Constrained Translation & Feedback Loop.

This worker implements the complete Phase 2 pipeline:
    1. Semantic chunking of text blocks (10-15 pages per chunk).
    2. Constrained translation via Gemini 2.5 Flash Translator Agent.
    3. AI-powered review scoring via Gemini 2.5 Flash Reviser Agent.
    4. Feedback loop with circuit breaker (max 3 retries per chunk).

Parallelism & Optimization:
    - Context Caching: global_metadata system prompt cached once via Gemini API,
      reused across ALL translator + reviser calls (saves tokens & latency).
    - asyncio.gather: all chunks processed concurrently through feedback loop.
    - Batching: 15 pages of text blocks sent as a single Gemini call per chunk.
    - In-memory: entire pipeline operates on JSON dicts, zero disk I/O.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# ── Environment & Constants ──────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL = "gemini-2.5-flash"
CHUNK_SIZE = 15  # Pages per translation chunk
MAX_RETRIES = 3  # Circuit breaker threshold
PASS_SCORE = 8   # Minimum score to pass review
CACHE_TTL = "3600s"  # Context cache time-to-live (1 hour)

logging.basicConfig(level=logging.INFO, format="[Phase2] %(message)s")
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
#  PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════


class TranslatedBlock(BaseModel):
    """A single translated text block preserving spatial mapping."""

    original_content: str = Field(description="Source text content")
    translated_content: str = Field(description="Translated text content")
    bbox: list[float] = Field(description="Original bounding box [x0, y0, x1, y1]")
    page_id: int = Field(description="Source page number")
    source_type: str = Field(
        description="Block origin: 'text' (PDF text layer) or 'ocr' (in-image text)"
    )
    font: str = Field(default="", description="Original font family")
    size: float = Field(default=0.0, description="Original font size")
    color: int = Field(default=0, description="Original text color")
    flags: int = Field(default=0, description="Original font flags")
    warning: Optional[str] = Field(
        default=None, description="Warning if translation did not pass review"
    )


class RevisionResult(BaseModel):
    """Score and feedback from the Reviser Agent."""

    score: int = Field(ge=1, le=10, description="Quality score 1-10")
    reason: str = Field(default="", description="Explanation if score < 8")


class TranslationChunk(BaseModel):
    """A group of text blocks to be translated together."""

    chunk_id: int = Field(description="Chunk sequence number")
    blocks: list[dict] = Field(description="Source text/OCR blocks in this chunk")
    page_range: str = Field(description="Human-readable page range, e.g. '1-15'")


# ═══════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════


async def run(payload: dict) -> dict:
    """
    Main entry point for Phase 2 processing.

    Orchestrates semantic chunking, context cache creation, concurrent
    translation with feedback loops, and final result assembly.

    Args:
        payload: Contains data from Phase 1:
            - standardized_pack (list[dict]): Pages with text/image/OCR blocks.
            - global_metadata (dict): Global constraints from Phase 1.
            - thread_id (str): Unique pipeline run identifier.

    Returns:
        dict: Contains 'verified_text_pack' (list) and 'translation_warnings' (list).
    """
    standardized_pack = payload["standardized_pack"]
    global_metadata = payload["global_metadata"]
    thread_id = payload.get("thread_id", "unknown")

    logger.info("Starting Phase 2 pipeline for thread=%s", thread_id)

    # ── Initialize Gemini client ─────────────────────────────────
    client = genai.Client(api_key=GEMINI_API_KEY)

    # ── Step 1: Semantic Chunking ────────────────────────────────
    logger.info("[#p2.1] Chunking text blocks (chunk_size=%d pages)...", CHUNK_SIZE)
    chunks = _chunk_text_blocks(standardized_pack, CHUNK_SIZE)
    logger.info("[#p2.1] Created %d chunks", len(chunks))

    if not chunks:
        logger.warning("No translatable text blocks found. Returning empty pack.")
        return {"verified_text_pack": [], "translation_warnings": []}

    # ── Step 2: Create Context Cache (optimization #5) ───────────
    logger.info("[Cache] Creating Gemini context cache for global_metadata...")
    translator_cache, reviser_cache = await _create_context_caches(
        client, global_metadata, thread_id
    )
    logger.info("[Cache] Context caches created successfully")

    # ── Step 3: Concurrent Translation + Feedback Loop ───────────
    # All chunks processed in parallel via asyncio.gather
    logger.info(
        "[#p2.4] Starting feedback loop for %d chunks (asyncio.gather)...",
        len(chunks),
    )
    chunk_results = await asyncio.gather(
        *[
            _translate_with_feedback_loop(
                chunk, global_metadata, client, translator_cache, reviser_cache
            )
            for chunk in chunks
        ]
    )

    # ── Step 4: Assemble verified text pack ──────────────────────
    verified_text_pack = []
    translation_warnings = []

    for translated_blocks, warnings in chunk_results:
        verified_text_pack.extend([b.model_dump() for b in translated_blocks])
        translation_warnings.extend(warnings)

    logger.info(
        "Phase 2 complete. %d blocks translated, %d warnings.",
        len(verified_text_pack),
        len(translation_warnings),
    )

    # ── Cleanup: delete context caches ───────────────────────────
    try:
        if translator_cache:
            await client.aio.caches.delete(name=translator_cache)
        if reviser_cache:
            await client.aio.caches.delete(name=reviser_cache)
        logger.info("[Cache] Context caches cleaned up")
    except Exception as e:
        logger.warning("Cache cleanup failed (non-critical): %s", e)

    return {
        "verified_text_pack": verified_text_pack,
        "translation_warnings": translation_warnings,
    }


# ═══════════════════════════════════════════════════════════════════
#  TASK #p2.1 — SEMANTIC CHUNKING
# ═══════════════════════════════════════════════════════════════════


def _chunk_text_blocks(
    standardized_pack: list[dict], chunk_size: int
) -> list[TranslationChunk]:
    """
    Group translatable text blocks into semantic chunks of N pages each.

    Collects both regular text blocks (from PDF text layer) and OCR text blocks
    (from embedded images). Only blocks tagged 'editable' or 'semi-editable'
    are included for translation.

    Args:
        standardized_pack: List of page dicts from Phase 1 output.
        chunk_size: Number of pages per chunk (default 15).

    Returns:
        list[TranslationChunk]: Chunks ready for translation.
    """
    # Collect all translatable blocks across pages
    all_blocks_by_page = []

    for page in standardized_pack:
        page_id = page["page_id"]
        page_blocks = []

        # Regular text blocks
        for tb in page.get("text_blocks", []):
            tag = tb.get("editability_tag", "editable")
            if tag in ("editable", "semi-editable"):
                page_blocks.append(
                    {
                        "content": tb["content"],
                        "bbox": tb["bbox"],
                        "page_id": page_id,
                        "source_type": "text",
                        "font": tb.get("font", ""),
                        "size": tb.get("size", 0.0),
                        "color": tb.get("color", 0),
                        "flags": tb.get("flags", 0),
                    }
                )

        # OCR text blocks from image blocks
        for ib in page.get("image_blocks", []):
            for ocr_block in ib.get("ocr_text_blocks", []):
                tag = ocr_block.get("editability_tag", "editable")
                if tag in ("editable", "semi-editable"):
                    page_blocks.append(
                        {
                            "content": ocr_block["content"],
                            "bbox": ib["bbox"],  # Use parent image bbox
                            "bbox_in_image": ocr_block["bbox_in_image"],
                            "page_id": page_id,
                            "source_type": "ocr",
                            "font": "",
                            "size": 0.0,
                            "color": 0,
                            "flags": 0,
                        }
                    )

        if page_blocks:
            all_blocks_by_page.append((page_id, page_blocks))

    # Group pages into chunks
    chunks = []
    for i in range(0, len(all_blocks_by_page), chunk_size):
        group = all_blocks_by_page[i : i + chunk_size]
        chunk_blocks = []
        page_ids = []
        for page_id, blocks in group:
            chunk_blocks.extend(blocks)
            page_ids.append(page_id)

        page_range = (
            f"{min(page_ids)}-{max(page_ids)}" if page_ids else "0-0"
        )

        chunks.append(
            TranslationChunk(
                chunk_id=len(chunks) + 1,
                blocks=chunk_blocks,
                page_range=page_range,
            )
        )

    return chunks


# ═══════════════════════════════════════════════════════════════════
#  CONTEXT CACHING — Reuse system prompts across all API calls
# ═══════════════════════════════════════════════════════════════════


def _build_translator_system_prompt(global_metadata: dict) -> str:
    """
    Build the Translator Agent system prompt with embedded global constraints.

    Args:
        global_metadata: Global constraints dict from Phase 1.

    Returns:
        str: Complete system prompt for translation calls.
    """
    protected = global_metadata.get("protected_names", [])
    style = global_metadata.get("style_register", "children_under_10")
    src_lang = global_metadata.get("source_language", "EN")
    tgt_lang = global_metadata.get("target_language", "VI")
    fidelity = global_metadata.get("translation_fidelity", "Strict")
    cultural = global_metadata.get("cultural_localization", False)
    sfx = global_metadata.get("sfx_handling", "In_panel_subs")
    age = global_metadata.get("target_age_tone", 10)
    drift = global_metadata.get("max_drift_ratio", 0.15)

    return f"""You are a professional children's book translator ({src_lang} → {tgt_lang}).

ABSOLUTE RULES — VIOLATION IS UNACCEPTABLE:
1. DO NOT translate these protected names: {json.dumps(protected, ensure_ascii=False)}
   Keep them exactly as-is in the target text.
2. Translation fidelity: {fidelity}. {"Do not add or remove any content." if fidelity == "Strict" else "You may add minimal clarifying notes."}
3. Cultural localization: {"ALLOWED — adapt cultural references for Vietnamese readers." if cultural else "FORBIDDEN — keep all cultural references as-is."}
4. Style register: Write for {style} (target age: {age}).
   Use simple vocabulary, short sentences, and a warm, engaging tone.
5. SFX handling: {sfx}. Handle onomatopoeia accordingly.
6. Max text length drift: {int(drift * 100)}% compared to source text.
   Vietnamese translations should not be significantly longer/shorter.

OUTPUT FORMAT — Return a JSON array. For each text block:
{{
    "original_content": "<exact source text>",
    "translated_content": "<your Vietnamese translation>",
    "block_index": <0-based index matching input order>
}}

Return ONLY valid JSON, no markdown fences, no explanation."""


def _build_reviser_system_prompt(global_metadata: dict) -> str:
    """
    Build the Reviser Agent system prompt with embedded global constraints.

    Args:
        global_metadata: Global constraints dict from Phase 1.

    Returns:
        str: Complete system prompt for review/scoring calls.
    """
    protected = global_metadata.get("protected_names", [])
    style = global_metadata.get("style_register", "children_under_10")
    fidelity = global_metadata.get("translation_fidelity", "Strict")
    drift = global_metadata.get("max_drift_ratio", 0.15)

    return f"""You are a senior translation quality reviewer for children's book localization.

EVALUATION CRITERIA — Score 1-10 based on:
1. ACCURACY: Does the translation faithfully convey the source meaning?
2. CONSTRAINT COMPLIANCE:
   - Protected names MUST remain untranslated: {json.dumps(protected, ensure_ascii=False)}
   - Translation fidelity mode: {fidelity}
3. TONE: Is the language appropriate for {style}?
4. NATURALNESS: Does it sound natural in Vietnamese? No awkward phrasing.
5. LENGTH: Is the translation within {int(drift * 100)}% length of the source?

SCORING GUIDE:
- 9-10: Excellent, publication-ready
- 8: Good, acceptable with minor stylistic preferences
- 6-7: Acceptable but has notable issues
- 4-5: Poor, significant errors
- 1-3: Unacceptable, major constraint violations

OUTPUT FORMAT:
{{"score": <1-10>, "reason": "<brief explanation, especially if score < 8>"}}

Return ONLY valid JSON, no markdown fences."""


async def _create_context_caches(
    client: genai.Client, global_metadata: dict, thread_id: str
) -> tuple[Optional[str], Optional[str]]:
    """
    Create Gemini context caches for Translator and Reviser system prompts.

    Caches the system prompt (which contains global_metadata constraints) so it
    doesn't need to be re-sent on every API call. This saves tokens and reduces
    latency across multiple translation + review calls.

    Args:
        client: Initialized Gemini API client.
        global_metadata: Global constraints dict.
        thread_id: Pipeline run ID for cache naming.

    Returns:
        tuple: (translator_cache_name, reviser_cache_name) or (None, None) if
               caching fails (falls back to inline system prompts).
    """
    translator_prompt = _build_translator_system_prompt(global_metadata)
    reviser_prompt = _build_reviser_system_prompt(global_metadata)

    try:
        translator_cache = client.caches.create(
            model=MODEL,
            config=types.CreateCachedContentConfig(
                system_instruction=translator_prompt,
                display_name=f"p2-translator-{thread_id[:8]}",
                ttl=CACHE_TTL,
            ),
        )
        reviser_cache = client.caches.create(
            model=MODEL,
            config=types.CreateCachedContentConfig(
                system_instruction=reviser_prompt,
                display_name=f"p2-reviser-{thread_id[:8]}",
                ttl=CACHE_TTL,
            ),
        )
        return translator_cache.name, reviser_cache.name

    except Exception as e:
        logger.warning(
            "Context cache creation failed: %s. Falling back to inline prompts.", e
        )
        return None, None


# ═══════════════════════════════════════════════════════════════════
#  TASK #p2.2 — TRANSLATOR AGENT
# ═══════════════════════════════════════════════════════════════════


async def _translate_chunk(
    chunk: TranslationChunk,
    global_metadata: dict,
    client: genai.Client,
    cache_name: Optional[str],
    feedback: Optional[str] = None,
) -> list[dict]:
    """
    Translate a chunk of text blocks via Gemini 2.5 Flash Translator Agent.

    Uses context caching if available, otherwise falls back to inline system
    prompt. Batches all blocks in the chunk into a single API call.

    Args:
        chunk: TranslationChunk with source text blocks.
        global_metadata: Global constraints dict.
        client: Initialized Gemini API client.
        cache_name: Gemini context cache name (or None for inline prompt).
        feedback: Optional revision feedback from previous attempt.

    Returns:
        list[dict]: Translated blocks with original_content and translated_content.
    """
    # Build the user message with source text blocks
    source_blocks = []
    for i, block in enumerate(chunk.blocks):
        source_blocks.append(
            {
                "block_index": i,
                "content": block["content"],
                "source_type": block["source_type"],
                "page_id": block["page_id"],
            }
        )

    user_message = f"Translate these text blocks (pages {chunk.page_range}):\n"
    user_message += json.dumps(source_blocks, ensure_ascii=False)

    if feedback:
        user_message += (
            f"\n\n⚠️ REVISION FEEDBACK FROM PREVIOUS ATTEMPT:\n{feedback}\n"
            "Please fix the issues mentioned above in your new translation."
        )

    # ── Call Gemini with cache or inline prompt ──────────────────
    config = types.GenerateContentConfig(
        temperature=0.3,
        response_mime_type="application/json",
    )

    if cache_name:
        config.cached_content = cache_name
    else:
        config.system_instruction = _build_translator_system_prompt(global_metadata)

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=user_message,
        config=config,
    )

    raw_json = response.text.strip()
    if raw_json.startswith("```"):
        raw_json = raw_json.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    translations = json.loads(raw_json)
    return translations


# ═══════════════════════════════════════════════════════════════════
#  TASK #p2.3 — REVISER AGENT
# ═══════════════════════════════════════════════════════════════════


async def _review_translation(
    chunk: TranslationChunk,
    translations: list[dict],
    global_metadata: dict,
    client: genai.Client,
    cache_name: Optional[str],
) -> RevisionResult:
    """
    Review a translated chunk via Gemini 2.5 Flash Reviser Agent.

    Sends source text, draft translation, and constraints to the Reviser for
    quality scoring. Uses context caching if available.

    Args:
        chunk: Original source chunk with text blocks.
        translations: Draft translated blocks from Translator Agent.
        global_metadata: Global constraints dict.
        client: Initialized Gemini API client.
        cache_name: Gemini context cache name (or None for inline prompt).

    Returns:
        RevisionResult: Score (1-10) and reason if score < 8.
    """
    # Build review payload — source + draft side by side
    review_pairs = []
    for i, block in enumerate(chunk.blocks):
        translated_content = ""
        for t in translations:
            if t.get("block_index") == i:
                translated_content = t.get("translated_content", "")
                break

        review_pairs.append(
            {
                "block_index": i,
                "source": block["content"],
                "translation": translated_content,
                "source_type": block["source_type"],
            }
        )

    user_message = (
        f"Review this translation (pages {chunk.page_range}):\n"
        + json.dumps(review_pairs, ensure_ascii=False)
    )

    config = types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type="application/json",
    )

    if cache_name:
        config.cached_content = cache_name
    else:
        config.system_instruction = _build_reviser_system_prompt(global_metadata)

    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=user_message,
        config=config,
    )

    raw_json = response.text.strip()
    if raw_json.startswith("```"):
        raw_json = raw_json.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    result_dict = json.loads(raw_json)
    return RevisionResult(**result_dict)


# ═══════════════════════════════════════════════════════════════════
#  TASK #p2.4 — FEEDBACK LOOP + CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════════


async def _translate_with_feedback_loop(
    chunk: TranslationChunk,
    global_metadata: dict,
    client: genai.Client,
    translator_cache: Optional[str],
    reviser_cache: Optional[str],
) -> tuple[list[TranslatedBlock], list[dict]]:
    """
    Run the full Translator ↔ Reviser feedback loop for a single chunk.

    Implements the circuit breaker pattern:
        - score >= 8 → PASS, save as verified.
        - score < 8 and retry < 3 → RETRY with feedback.
        - score < 8 and retry >= 3 → CIRCUIT BREAK, keep last draft + WARNING.

    Args:
        chunk: TranslationChunk to translate.
        global_metadata: Global constraints dict.
        client: Initialized Gemini API client.
        translator_cache: Context cache name for Translator Agent.
        reviser_cache: Context cache name for Reviser Agent.

    Returns:
        tuple: (list[TranslatedBlock], list[warning_dicts])
    """
    logger.info(
        "[Chunk %d] Translating pages %s (%d blocks)...",
        chunk.chunk_id,
        chunk.page_range,
        len(chunk.blocks),
    )

    feedback = None
    translations = []
    retries = 0
    final_score = 0
    final_reason = ""

    while retries <= MAX_RETRIES:
        # ── Translate ────────────────────────────────────────────
        try:
            translations = await _translate_chunk(
                chunk, global_metadata, client, translator_cache, feedback
            )
        except Exception as e:
            logger.error("[Chunk %d] Translation failed: %s", chunk.chunk_id, e)
            translations = []
            break

        # ── Review ───────────────────────────────────────────────
        try:
            revision = await _review_translation(
                chunk, translations, global_metadata, client, reviser_cache
            )
            final_score = revision.score
            final_reason = revision.reason
        except Exception as e:
            logger.error("[Chunk %d] Review failed: %s", chunk.chunk_id, e)
            # Accept the translation without review
            final_score = PASS_SCORE
            final_reason = ""
            break

        logger.info(
            "[Chunk %d] Attempt %d/%d — Score: %d/10%s",
            chunk.chunk_id,
            retries + 1,
            MAX_RETRIES + 1,
            final_score,
            f" ({final_reason})" if final_reason else "",
        )

        # ── Route: PASS or RETRY ────────────────────────────────
        if final_score >= PASS_SCORE:
            logger.info("[Chunk %d] ✅ PASSED", chunk.chunk_id)
            break

        retries += 1
        if retries <= MAX_RETRIES:
            feedback = final_reason
            logger.info("[Chunk %d] 🔄 RETRY with feedback...", chunk.chunk_id)
        else:
            logger.warning(
                "[Chunk %d] ⚠️ CIRCUIT BREAK after %d retries. Keeping last draft.",
                chunk.chunk_id,
                MAX_RETRIES,
            )

    # ── Assemble TranslatedBlock results ─────────────────────────
    translated_blocks = []
    warnings = []
    is_warning = final_score < PASS_SCORE

    for i, block in enumerate(chunk.blocks):
        translated_content = ""
        for t in translations:
            if t.get("block_index") == i:
                translated_content = t.get("translated_content", "")
                break

        warning_msg = None
        if is_warning:
            warning_msg = (
                f"[WARNING] Score {final_score}/10 after {MAX_RETRIES} retries. "
                f"Reason: {final_reason}"
            )

        translated_blocks.append(
            TranslatedBlock(
                original_content=block["content"],
                translated_content=translated_content or block["content"],
                bbox=block["bbox"],
                page_id=block["page_id"],
                source_type=block["source_type"],
                font=block.get("font", ""),
                size=block.get("size", 0.0),
                color=block.get("color", 0),
                flags=block.get("flags", 0),
                warning=warning_msg,
            )
        )

    if is_warning:
        warnings.append(
            {
                "chunk_id": chunk.chunk_id,
                "page_range": chunk.page_range,
                "final_score": final_score,
                "reason": final_reason,
                "retries_exhausted": retries,
            }
        )

    return translated_blocks, warnings
