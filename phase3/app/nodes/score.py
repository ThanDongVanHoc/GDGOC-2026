"""Score node — parallel LLM-based cultural density scoring with grouping.

Assigns a cultural-importance score (0-10) to each text block via
batched LLM calls, then groups blocks into cascading translation chunks.
Scoring prompts are style-aware via ``prompt_builder``.
"""

import asyncio
import json
import logging
import math
from typing import Any

from openai import OpenAI

from app.prompt_builder import build_scoring_system_prompt
from app.state import Phase3State
from core.models import GlobalMetadata

logger = logging.getLogger(__name__)

_FPT_MODEL: str = "gemma-4-31B-it"
_BATCH_SIZE: int = 15


async def _score_blocks_llm(
    blocks: list[dict[str, Any]],
    client: OpenAI | None,
    metadata: GlobalMetadata,
) -> list[int]:
    """Score blocks for cultural density using parallelized LLM batches.

    Args:
        blocks: Normalized text blocks with ``english_content`` key.
        client: OpenAI-compatible client, or ``None`` to skip scoring.
        metadata: Global metadata used to build style-aware scoring prompt.

    Returns:
        A list of integer scores (0-10), one per block.
    """
    if not client:
        logger.warning("[Phase3:Score] Client is None. Skipping LLM scoring; defaulting to scores=0.")
        return [0] * len(blocks)

    scores = [0] * len(blocks)
    system_prompt = build_scoring_system_prompt(metadata)

    batches: list[tuple[int, list[dict[str, Any]]]] = []
    for i in range(0, len(blocks), _BATCH_SIZE):
        batches.append((i, blocks[i : i + _BATCH_SIZE]))

    async def _process_batch(
        start_idx: int, batch_blocks: list[dict[str, Any]]
    ) -> tuple[int, list[dict[str, Any]]]:
        prompt_data = [
            {"id": j, "text": b["english_content"]}
            for j, b in enumerate(batch_blocks)
        ]
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=_FPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(prompt_data, ensure_ascii=False),
                    },
                ],
                temperature=0.1,
                max_tokens=1024,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = "\n".join(
                    line
                    for line in raw.split("\n")
                    if not line.strip().startswith("```")
                )
            return start_idx, json.loads(raw)
        except Exception as exc:
            logger.warning("[Phase3:Score] Batch scoring failed: %s", exc)
            return start_idx, []

    results = await asyncio.gather(
        *[_process_batch(i, b) for i, b in batches]
    )
    for start_idx, items in results:
        for item in items:
            idx = start_idx + item.get("id", 0)
            if idx < len(scores):
                scores[idx] = int(item.get("score", 0))
    return scores


def _build_groups(
    num_blocks: int, max_groups: int, scores: list[int]
) -> list[dict[str, Any]]:
    """Chunk blocks into cascading translation groups.

    Args:
        num_blocks: Total number of blocks.
        max_groups: Maximum number of groups to create.
        scores: Cultural density scores per block.

    Returns:
        A list of group dicts with ``indices`` and ``score`` keys.
    """
    actual_groups_count = min(max_groups, num_blocks) if num_blocks > 0 else 1
    chunk_size = math.ceil(num_blocks / actual_groups_count)

    groups: list[dict[str, Any]] = []
    for i in range(0, num_blocks, chunk_size):
        idxs = list(range(i, min(i + chunk_size, num_blocks)))
        if idxs:
            groups.append({
                "indices": idxs,
                "score": max(scores[idx] for idx in idxs),
            })
    return groups


async def score_node(state: Phase3State) -> dict[str, Any]:
    """LangGraph node: score blocks and build cascading groups.

    Reads:
        ``state["blocks"]``, ``state["client"]``,
        ``state["global_metadata"]``, ``state["max_groups"]``

    Writes:
        ``scores`` — list of int scores per block.
        ``groups`` — list of group dicts for cascading translation.

    Args:
        state: Current graph state.

    Returns:
        Partial state update with ``scores`` and ``groups``.
    """
    blocks = state.get("blocks", [])
    client = state.get("client")
    metadata = state.get("global_metadata", GlobalMetadata())
    max_groups = state.get("max_groups", 30)

    scores = await _score_blocks_llm(blocks, client, metadata)
    groups = _build_groups(len(blocks), max_groups, scores)

    logger.info(
        "[Phase3:Score] Scored %d blocks into %d groups.",
        len(blocks),
        len(groups),
    )
    return {"scores": scores, "groups": groups}
