"""OmniLocal — Phase 3 Worker: Cultural Localization & Butterfly Effect.
Cascading Denoising Execution version.
"""

import asyncio
import json
import logging
import math
import os
import time
from typing import Any

from openai import OpenAI
from core.models import Phase3InputPayload

logger = logging.getLogger(__name__)

_FPT_API_KEY: str = os.environ.get("FPT_API_KEY", "")
_FPT_BASE_URL: str = "https://mkp-api.fptcloud.com"
_FPT_MODEL: str = "gemma-4-31B-it"

_DEFAULT_CHAR_WIDTH_RATIO: float = 0.55
_LINE_HEIGHT_FACTOR: float = 1.2


def _normalize_text_pack(raw_text_pack: Any) -> list[dict[str, Any]]:
    """Return a flat list of text blocks with normalized keys."""
    blocks = []
    
    if isinstance(raw_text_pack, dict) and "pages" in raw_text_pack:
        for page in raw_text_pack["pages"]:
            pid = page.get("page_id", 0)
            for b in page.get("text_blocks", []):
                b["page_id"] = pid
                blocks.append(b)
    elif isinstance(raw_text_pack, list):
        for b in raw_text_pack:
            pid = b.get("page_id", 0)
            blocks.append(b)
            
    normalized = []
    for block in blocks:
        normalized.append({
            "original_content": block.get("translated_content", block.get("original_content", "")),
            "english_content": block.get("original_content", block.get("text", "")),
            "translated_content": block.get("translated_content", ""),
            "bbox": block.get("bbox", [0.0, 0.0, 0.0, 0.0]),
            "page_id": block.get("page_id", 1),
            "source_type": block.get("source_type", "text"),
            "font": block.get("font", ""),
            "size": block.get("size", 0.0),
            "color": block.get("color", 0),
            "flags": block.get("flags", 0),
            "warning": block.get("warning", None),
            "localized_content": ""
        })
    return normalized


async def _score_blocks_llm(blocks: list[dict[str, Any]], client: OpenAI | None) -> list[int]:
    """Parallelized block scoring."""
    if not client:
        return [0] * len(blocks)
        
    scores = [0] * len(blocks)
    BATCH_SIZE = 15
    batches = []
    for i in range(0, len(blocks), BATCH_SIZE):
        batches.append((i, blocks[i:i+BATCH_SIZE]))

    async def _process_batch(start_idx: int, batch_blocks: list[dict]) -> tuple[int, list]:
        prompt_data = [{"id": j, "text": b["english_content"]} for j, b in enumerate(batch_blocks)]
        system = (
            "You are a cultural evaluator. Rate each text block on a scale of 0 to 10 based on how much "
            "'Cultural Context' or 'Cultural Anchors' it contains (e.g., specific weather, holidays, "
            "foods, folklore entities, idioms).\n"
            "0 = Generic text. 10 = Heavy cultural context.\n"
            "Output EXACTLY a JSON array of objects: [{\"id\": 0, \"score\": 5}]"
        )
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=_FPT_MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(prompt_data, ensure_ascii=False)}],
                temperature=0.1,
                max_tokens=1024,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = "\n".join([line for line in raw.split("\n") if not line.strip().startswith("```")])
            return start_idx, json.loads(raw)
        except Exception as e:
            logger.warning("[Phase3] Batch scoring failed: %s", e)
            return start_idx, []

    results = await asyncio.gather(*[_process_batch(i, b) for i, b in batches])
    for start_idx, items in results:
        for item in items:
            idx = start_idx + item.get("id", 0)
            if idx < len(scores): scores[idx] = int(item.get("score", 0))
    return scores


async def run(payload: dict) -> dict:
    t_start = time.perf_counter()
    
    try:
        validated_payload = Phase3InputPayload(**payload)
        output_phase_2 = validated_payload.output_phase_2 or {}
        if isinstance(output_phase_2, dict):
             raw_text_pack = output_phase_2.get("verified_text_pack", validated_payload.verified_text_pack or {})
        else:
             raw_text_pack = validated_payload.verified_text_pack or {}
        source_pdf_path = validated_payload.source_pdf_path
        use_llm = validated_payload.use_llm
    except Exception as e:
        logger.error("[Phase3] Payload error: %s", e)
        raw_text_pack = payload.get("output_phase_2", {}).get("verified_text_pack", payload.get("verified_text_pack", {}))
        source_pdf_path = payload.get("source_pdf_path", "")
        use_llm = payload.get("use_llm", False)
        
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "core", "config.json")
    max_groups = 30
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                max_groups = json.load(f).get("cascading_max_groups", 30)
        except: pass

    blocks = _normalize_text_pack(raw_text_pack)
    client = OpenAI(api_key=_FPT_API_KEY, base_url=_FPT_BASE_URL) if (use_llm and _FPT_API_KEY) else None
    
    # 1. Scoring
    scores = await _score_blocks_llm(blocks, client)

    # 2. Grouping
    num_blocks = len(blocks)
    actual_groups_count = min(max_groups, num_blocks) if num_blocks > 0 else 1
    chunk_size = math.ceil(num_blocks / actual_groups_count)
    
    groups = []
    for i in range(0, num_blocks, chunk_size):
        idxs = list(range(i, min(i + chunk_size, num_blocks)))
        if idxs: groups.append({"indices": idxs, "score": max(scores[idx] for idx in idxs)})
        
    # 3. Cascading Tiered Parallel Translation
    logger.info("[Phase3] Starting Tiered Parallel Localization...")
    context_established = []
    system_msg = (
        "You are an expert Vietnamese cultural localizer. Translate English blocks into natural Vietnamese.\n"
        "- CRITICALLY IMPORTANT: Localize Western objects (e.g., 'snow', 'snowman') to Vietnamese equivalents (e.g., 'mưa rào', 'bùn lầy').\n"
        "- Respect 'Context of previously localized parts' for consistency.\n"
        "Output EXACTLY a JSON array: [{\"id\": <id>, \"localization\": \"<translated_text>\"}]"
    )

    async def _translate_group(g: dict, ctx: str) -> dict[int, str]:
        indices = g["indices"]
        payload_data = [{"id": idx, "english": blocks[idx]["english_content"], "raw_translation": blocks[idx]["translated_content"]} for idx in indices]
        if not client: return {idx: blocks[idx]["translated_content"] for idx in indices}
        user_msg = f"Context of previously localized parts:\n{ctx}\n\nBlocks to translate:\n{json.dumps(payload_data, ensure_ascii=False)}"
        try:
            resp = await asyncio.to_thread(client.chat.completions.create, model=_FPT_MODEL, messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": user_msg}], temperature=0.2, max_tokens=2048)
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"): raw = "\n".join([l for l in raw.split("\n") if not l.strip().startswith("```")])
            return {item["id"]: item.get("localization", "") for item in json.loads(raw) if "id" in item}
        except: return {idx: blocks[idx]["translated_content"] for idx in indices}

    tier_map = {}
    for g in groups: tier_map.setdefault(g["score"], []).append(g)
    
    for score in sorted(tier_map.keys(), reverse=True):
        tier_groups = tier_map[score]
        ctx_str = "\n".join(context_established[-20:]) if context_established else "None"
        results = await asyncio.gather(*[_translate_group(g, ctx_str) for g in tier_groups])
        for i, ans_map in enumerate(results):
            for idx in tier_groups[i]["indices"]:
                b = blocks[idx]
                loc = ans_map.get(idx, b["translated_content"])
                b["localized_content"] = loc
                if b["english_content"].strip(): context_established.append(f"English: '{b['english_content']}' -> Localized: '{loc}'")

    # 4. Finalizing
    context_safe_pack = []
    overflow_warnings = []
    for i, b in enumerate(blocks):
        bbox, font_size = b["bbox"], b["size"]
        max_chars = 10000
        if len(bbox) == 4 and font_size > 0:
            bw, bh = abs(bbox[2] - bbox[0]), abs(bbox[3] - bbox[1])
            cw, lh = font_size * _DEFAULT_CHAR_WIDTH_RATIO, font_size * _LINE_HEIGHT_FACTOR
            if bw > 0 and bh > 0 and cw > 0:
                cpl, nl = max(1, math.floor(bw / cw)), max(1, math.floor(bh / lh))
                max_chars = max(1, cpl * nl)
        
        loc_text = b["localized_content"]
        if len(loc_text) > max_chars:
            overflow_warnings.append({"page_id": b["page_id"], "block_index": i, "original_content": b["original_content"], "localized_content": loc_text, "max_estimated_chars": max_chars, "actual_chars": len(loc_text), "overflow_ratio": round(len(loc_text) / max_chars, 2)})
        context_safe_pack.append({"original_content": b["original_content"], "localized_content": loc_text, "bbox": b["bbox"], "page_id": b["page_id"], "source_type": b["source_type"], "font": b["font"], "size": b["size"], "color": b["color"], "flags": b["flags"], "warning": b["warning"]})

    elapsed_ms = (time.perf_counter() - t_start) * 1000
    logger.info("[Phase3] Pipeline complete in %.1f ms.", elapsed_ms)
    return {"output_phase_3": {"context_safe_localized_text_pack": context_safe_pack, "entity_graph": {}, "localization_log": [], "Images": [], "source_pdf_path": source_pdf_path}, "localization_warnings": overflow_warnings}
