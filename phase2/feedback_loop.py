"""
Task #p2.4: Feedback Loop Engine — Translator ↔ Reviser negotiation.

Implements the while loop that alternates between the Translator Agent
and the Reviser Agent until the translation quality meets the threshold
or the circuit breaker trips after max retries.
"""

import logging

from phase2.models import (
    SemanticChunk,
    TranslatedBlock,
    VerifiedTextPack,
    WarningLevel,
)
from phase2.reviser_agent import revise_translation
from phase2.translator_agent import translate_blocks

logger = logging.getLogger(__name__)

PASS_THRESHOLD = 8.0
MAX_RETRIES = 3


def process_chunk(
    chunk: SemanticChunk,
    global_metadata: dict,
    api_key: str,
) -> VerifiedTextPack:
    """Processes a single semantic chunk through the translation feedback loop.

    Runs the Translator Agent to produce a draft, then the Reviser Agent
    to evaluate it. If the score is below the threshold, sends feedback
    back to the Translator for a retry. Continues until:
    - The score meets the PASS_THRESHOLD (>= 8), or
    - MAX_RETRIES (3) are exhausted (circuit breaker trips).

    Args:
        chunk: A semantic chunk containing source text blocks to translate.
        global_metadata: Global metadata constraints dictionary.
        api_key: Gemini API key for authentication.

    Returns:
        VerifiedTextPack: Contains translated blocks with quality scores,
            and a list of warning indices for blocks that failed review.
    """
    text_blocks = chunk.text_blocks
    original_texts = [block.content for block in text_blocks]

    translations: list[str] = []
    best_score = 0.0
    best_translations: list[str] = []
    best_reason = ""
    feedback = ""

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(
            "Chunk %d: Translation attempt %d/%d",
            chunk.chunk_id,
            attempt,
            MAX_RETRIES,
        )

        # Step 1: Translate
        translations = translate_blocks(
            text_blocks=text_blocks,
            global_metadata=global_metadata,
            api_key=api_key,
            previous_feedback=feedback,
        )

        # Ensure translation count matches source count
        while len(translations) < len(original_texts):
            translations.append(original_texts[len(translations)])
        translations = translations[: len(original_texts)]

        # Step 2: Revise
        revision = revise_translation(
            original_texts=original_texts,
            translated_texts=translations,
            global_metadata=global_metadata,
            api_key=api_key,
        )

        logger.info(
            "Chunk %d attempt %d: score=%.1f, reason=%s",
            chunk.chunk_id,
            attempt,
            revision.score,
            revision.reason,
        )

        # Track the best attempt
        if revision.score > best_score:
            best_score = revision.score
            best_translations = translations[:]
            best_reason = revision.reason

        # Step 3: Check pass threshold
        if revision.score >= PASS_THRESHOLD:
            logger.info(
                "Chunk %d PASSED on attempt %d with score %.1f",
                chunk.chunk_id,
                attempt,
                revision.score,
            )
            return _build_verified_pack(
                chunk=chunk,
                translations=translations,
                score=revision.score,
                reason=revision.reason,
                warning_level=WarningLevel.NONE,
            )

        # Step 4: Prepare feedback for retry
        feedback = revision.reason

    # Circuit breaker: use best translations with WARNING tag
    logger.warning(
        "Chunk %d CIRCUIT BREAK after %d attempts. Best score: %.1f",
        chunk.chunk_id,
        MAX_RETRIES,
        best_score,
    )

    return _build_verified_pack(
        chunk=chunk,
        translations=best_translations if best_translations else translations,
        score=best_score,
        reason=best_reason,
        warning_level=WarningLevel.WARNING,
    )


def _build_verified_pack(
    chunk: SemanticChunk,
    translations: list[str],
    score: float,
    reason: str,
    warning_level: WarningLevel,
) -> VerifiedTextPack:
    """Assembles a VerifiedTextPack from translation results.

    Combines the original text block metadata with translated content,
    quality scores, and warning tags into the final output format.

    Args:
        chunk: The original semantic chunk with source text blocks.
        translations: List of translated strings.
        score: The final quality score from the reviser.
        reason: The revision reason (empty if passed).
        warning_level: Whether to tag this chunk with a warning.

    Returns:
        VerifiedTextPack: The packaged result ready for API delivery.
    """
    translated_blocks: list[TranslatedBlock] = []
    warning_indices: list[int] = []

    for i, block in enumerate(chunk.text_blocks):
        translated_content = (
            translations[i] if i < len(translations) else block.content
        )

        translated_blocks.append(
            TranslatedBlock(
                original_content=block.content,
                translated_content=translated_content,
                bbox=block.bbox,
                font=block.font,
                size=block.size,
                color=block.color,
                flags=block.flags,
                editability_tag=block.editability_tag,
                score=score,
                warning=warning_level,
                revision_reason=reason if warning_level == WarningLevel.WARNING else "",
            )
        )

        if warning_level == WarningLevel.WARNING:
            warning_indices.append(i)

    return VerifiedTextPack(
        chunk_id=chunk.chunk_id,
        translated_blocks=translated_blocks,
        warnings=warning_indices,
    )


def process_all_chunks(
    chunks: list[SemanticChunk],
    global_metadata: dict,
    api_key: str,
) -> list[VerifiedTextPack]:
    """Processes all semantic chunks through the translation feedback loop.

    Iterates through each chunk sequentially, running the full
    Translator ↔ Reviser negotiation loop for each one.

    Args:
        chunks: List of semantic chunks to process.
        global_metadata: Global metadata constraints dictionary.
        api_key: Gemini API key for authentication.

    Returns:
        list[VerifiedTextPack]: List of verified text packs, one per chunk.
    """
    results: list[VerifiedTextPack] = []

    for chunk in chunks:
        result = process_chunk(chunk, global_metadata, api_key)
        results.append(result)

    return results
