"""Translate node — cascading tiered parallel localization.

Executes the cascading denoising translation: high-cultural-density groups
are translated first, and their outputs feed as context into lower-density
groups. The system prompt is built dynamically from ``global_metadata``.
"""

import asyncio
import json
import logging
from typing import Any

from openai import OpenAI

from app.prompt_builder import build_localization_system_prompt
from app.state import Phase3State
from core.models import GlobalMetadata

logger = logging.getLogger(__name__)

_FPT_MODEL: str = "gemma-4-31B-it"


async def _translate_group(
    group: dict[str, Any],
    blocks: list[dict[str, Any]],
    context_str: str,
    system_msg: str,
    client: OpenAI | None,
) -> dict[int, str]:
    """Translate a single group of blocks using the LLM.

    Args:
        group: Group dict with ``indices`` key.
        blocks: Full list of normalized blocks.
        context_str: Stringified context from previously localized blocks.
        system_msg: Style-aware system prompt.
        client: OpenAI-compatible client, or ``None`` for passthrough.

    Returns:
        A mapping of block index → localized text.
    """
    indices = group["indices"]
    payload_data = [
        {
            "id": idx,
            "english": blocks[idx]["english_content"],
            "raw_translation": blocks[idx]["translated_content"],
        }
        for idx in indices
    ]

    if not client:
        logger.warning("[Phase3:Translate] Client is None. Passthrough mode enabled.")
        return {idx: blocks[idx]["translated_content"] for idx in indices}

    user_msg = (
        f"Context of previously localized parts:\n{context_str}\n\n"
        f"Blocks to translate:\n"
        f"{json.dumps(payload_data, ensure_ascii=False)}"
    )

    try:
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model=_FPT_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(
                line
                for line in raw.split("\n")
                if not line.strip().startswith("```")
            )
        return {
            item["id"]: item.get("localization", "")
            for item in json.loads(raw)
            if "id" in item
        }
    except Exception:
        return {idx: blocks[idx]["translated_content"] for idx in indices}


async def translate_node(state: Phase3State) -> dict[str, Any]:
    """LangGraph node: cascading tiered parallel translation.

    Groups are processed in tiers from highest cultural score to lowest.
    Within each tier, groups are translated in parallel. Completed
    translations accumulate as context for subsequent tiers.

    Reads:
        ``state["blocks"]``, ``state["groups"]``, ``state["client"]``,
        ``state["global_metadata"]``

    Writes:
        ``blocks`` — blocks with ``localized_content`` populated.
        ``context_established`` — running localization context list.

    Args:
        state: Current graph state.

    Returns:
        Partial state update with ``blocks`` and ``context_established``.
    """
    blocks = state.get("blocks", [])
    groups = state.get("groups", [])
    client = state.get("client")
    metadata = state.get("global_metadata", GlobalMetadata())

    system_msg = build_localization_system_prompt(metadata)
    context_established: list[str] = []

    logger.info("[Phase3:Translate] Starting Tiered Parallel Localization...")

    # Build tier map: score → list of groups
    tier_map: dict[int, list[dict[str, Any]]] = {}
    for group in groups:
        tier_map.setdefault(group["score"], []).append(group)

    # Process tiers from highest score to lowest
    for score in sorted(tier_map.keys(), reverse=True):
        tier_groups = tier_map[score]
        ctx_str = (
            "\n".join(context_established[-20:])
            if context_established
            else "None"
        )
        results = await asyncio.gather(
            *[
                _translate_group(g, blocks, ctx_str, system_msg, client)
                for g in tier_groups
            ]
        )
        for i, ans_map in enumerate(results):
            for idx in tier_groups[i]["indices"]:
                block = blocks[idx]
                loc = ans_map.get(idx, block["translated_content"])
                block["localized_content"] = loc
                if block["english_content"].strip():
                    context_established.append(
                        f"English: '{block['english_content']}' "
                        f"-> Localized: '{loc}'"
                    )

    return {"blocks": blocks, "context_established": context_established}
