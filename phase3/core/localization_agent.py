"""Localization Agent — LLM-backed cultural entity replacement (Task #p3.2).

Uses FPT Marketplace (OpenAI-compatible) to propose Vietnamese-appropriate
replacements for Western cultural entities. Falls back to a deterministic
rules-based generator when the LLM is unavailable.

The agent respects global_metadata constraints:
    - protected_names: never renamed
    - never_change_rules: free-text immutability constraints
    - lock_character_color: blocks colour-related changes
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from core.models import LocalizationProposal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FPT Marketplace config
# ---------------------------------------------------------------------------

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_FPT_API_KEY: str = os.environ.get("FPT_API_KEY", "")
_FPT_BASE_URL: str = "https://mkp-api.fptcloud.com"
_FPT_MODEL: str = "gemma-4-31B-it"
_FPT_VLM_MODEL: str = "Qwen2.5-VL-7B-Instruct"

# Prompt file paths
_VLM_SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "vlm_system_prompt.txt")
_LOCALIZATION_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "localization_system_prompt.txt")
_EXTRACTION_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "extraction_system_prompt.txt")
_REWRITE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "rewrite_system_prompt.txt")


def _read_prompt_file(file_path: str, fallback_text: str) -> str:
    """Read prompt from file with absolute path resolution and fallback."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"[Agent] Failed to read prompt file {file_path}: {e}")
    else:
        logger.warning(f"[Agent] Prompt file not found: {file_path}. Using fallback.")
    return fallback_text

# ---------------------------------------------------------------------------
# Fallback Prompts (if files are missing)
# ---------------------------------------------------------------------------

_FALLBACK_LOCALIZATION_PROMPT = """\
You are a Vietnamese cultural localization expert for children's picture books.
Your task: Propose Vietnamese replacements for Western cultural entities.
Return a JSON array of proposals with "original", "proposed", and "rationale".
"""

_FALLBACK_EXTRACTION_PROMPT = """\
You are an entity extractor. Given a list of texts by page, extract ALL cultural entities.
Return a JSON array of objects: [{"name": "Entity Name", "type": "character|location|object", "pages": [1, 2]}]
"""

_FALLBACK_REWRITE_PROMPT = """\
You are a Vietnamese language expert. Translate the English sentence into Vietnamese,
replacing the specific cultural concept as requested. Output ONLY the new sentence.
"""


# ---------------------------------------------------------------------------
# Deterministic fallback proposals (no LLM needed)
# ---------------------------------------------------------------------------

_FALLBACK_PROPOSALS: list[dict[str, str]] = [
    {
        "original": "cottage",
        "proposed": "nhà tranh",
        "rationale": "'Cottage' là kiểu nhà phương Tây. 'Nhà tranh' gần gũi hơn với văn hóa làng quê Việt Nam.",
    },
    {
        "original": "cloak",
        "proposed": "áo tơi",
        "rationale": "'Cloak' là trang phục thời trung cổ phương Tây. 'Áo tơi' là trang phục chống mưa truyền thống Việt Nam.",
    },
    {
        "original": "Goblin",
        "proposed": "Yêu tinh",
        "rationale": "'Goblin' là quái vật phương Tây. 'Yêu tinh' là hình ảnh quen thuộc trong truyện cổ tích Việt Nam.",
    },
    {
        "original": "squirrel",
        "proposed": "con sóc",
        "rationale": "Giữ nghĩa nguyên bản nhưng dùng tiếng Việt cho tự nhiên hơn trong ngữ cảnh sách thiếu nhi.",
    },
    {
        "original": "cobblestone",
        "proposed": "đá cuội",
        "rationale": "'Cobblestone' là loại đường lát đá đặc trưng châu Âu. 'Đá cuội' gần gũi với ngữ cảnh Việt Nam.",
    },
    {
        "original": "meadowlark",
        "proposed": "chim sơn ca",
        "rationale": "'Meadowlark' là loài chim Bắc Mỹ. 'Chim sơn ca' là loài quen thuộc hơn với trẻ em Việt Nam.",
    },
]

# Deterministic entity keywords for fallback extraction (no LLM needed)
_DETERMINISTIC_ENTITY_KEYWORDS: list[dict[str, str]] = [
    {"name": "cottage", "type": "location"},
    {"name": "cloak", "type": "clothing"},
    {"name": "Goblin", "type": "character"},
    {"name": "squirrel", "type": "animal"},
    {"name": "cobblestone", "type": "object"},
    {"name": "meadowlark", "type": "animal"},
    {"name": "Dragon", "type": "character"},
    {"name": "sword", "type": "object"},
    {"name": "forest", "type": "location"},
    {"name": "village", "type": "location"},
    {"name": "kingdom", "type": "location"},
    {"name": "enchanted", "type": "event"},
    {"name": "mountains", "type": "location"},
    {"name": "Willowmere", "type": "location"},
    {"name": "Whispering Woods", "type": "location"},
    {"name": "crossroads", "type": "location"},
    {"name": "apron", "type": "clothing"},
    {"name": "satchel", "type": "object"},
    {"name": "rain", "type": "weather_entity"},
]


# ---------------------------------------------------------------------------
# Deterministic entity extraction (no LLM)
# ---------------------------------------------------------------------------


def extract_entities_deterministic(
    text_pack: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract entities from text blocks using keyword-based matching.

    Scans all text blocks for occurrences of known entity keywords
    defined in ``_DETERMINISTIC_ENTITY_KEYWORDS``. This is used as a
    fallback when LLM-based extraction is disabled or unavailable.

    Args:
        text_pack: The Verified Text Pack in nested page format.

    Returns:
        A list of entity dicts with 'name', 'type', and 'pages' keys.
    """
    entity_map: dict[str, dict[str, Any]] = {}

    for page in text_pack.get("pages", []):
        page_id = page.get("page_id", 0)

        for block in page.get("text_blocks", []):
            # Search in both Vietnamese and English content, using english_content from the normalizer 
            text = block.get("translated_content", block.get("text", ""))
            original = block.get("english_content", "")
            combined = f"{text} {original}".lower()

            for kw in _DETERMINISTIC_ENTITY_KEYWORDS:
                if kw["name"].lower() in combined:
                    name = kw["name"]
                    if name not in entity_map:
                        entity_map[name] = {
                            "name": name,
                            "type": kw["type"],
                            "pages": [],
                        }
                    if page_id not in entity_map[name]["pages"]:
                        entity_map[name]["pages"].append(page_id)

    logger.info(
        "[Agent] Deterministic extraction found %d entities.", len(entity_map)
    )
    return list(entity_map.values())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_proposals_llm(
    entity_names: list[dict[str, str]],
    global_metadata: dict[str, Any],
    qa_feedback: dict | None = None,
) -> list[LocalizationProposal]:
    """Generate localization proposals using the FPT Marketplace LLM.

    Sends the entity list to the LLM with cultural context and constraints.
    If the LLM call fails, falls back to deterministic proposals.

    Args:
        entity_names: List of dicts with 'name', 'type', and 'pages' keys.
        global_metadata: Global constraints from Phase 1.
        qa_feedback: Optional QA feedback from a previous run.

    Returns:
        A list of LocalizationProposal objects.
    """
    protected = global_metadata.get("protected_names", [])
    never_change = global_metadata.get("never_change_rules", [])

    # Build the system prompt with constraints
    prompt_tpl = _read_prompt_file(_LOCALIZATION_PROMPT_PATH, _FALLBACK_LOCALIZATION_PROMPT)
    system = prompt_tpl.format(
        protected_names=json.dumps(protected),
        never_change_rules=json.dumps(never_change),
    )

    # Build user prompt
    user_msg = _build_user_prompt(entity_names, qa_feedback)

    try:
        client = OpenAI(api_key=_FPT_API_KEY, base_url=_FPT_BASE_URL)
        response = client.chat.completions.create(
            model=_FPT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=2048,
        )

        raw = response.choices[0].message.content.strip()
        logger.info("[Agent] LLM raw response length: %d chars", len(raw))

        proposals = _parse_llm_response(raw, entity_names, protected)
        logger.info(
            "[Agent] LLM generated %d proposals.", len(proposals)
        )
        return proposals

    except Exception as e:
        logger.warning(
            "[Agent] LLM call failed: %s. Using fallback proposals.", e
        )
        return generate_proposals_fallback(entity_names, protected)


def extract_entities_llm(texts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract cultural entities from text using the LLM natively.

    Replaces the reliance on the Phase 2 output giving entities.
    
    Args:
        texts: A list of dicts with 'page_id' and 'text'.
    
    Returns:
        A list of entity dictionaries with 'name', 'type', and 'pages'.
    """
    system = _read_prompt_file(_EXTRACTION_PROMPT_PATH, _FALLBACK_EXTRACTION_PROMPT)
    user_msg = json.dumps(texts, ensure_ascii=False)
    
    try:
        client = OpenAI(api_key=_FPT_API_KEY, base_url=_FPT_BASE_URL)
        response = client.chat.completions.create(
            model=_FPT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        
        raw = response.choices[0].message.content.strip()
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)
            
        entities = json.loads(cleaned)
        if isinstance(entities, list):
            return entities
        return []
    except Exception as e:
        logger.warning("[Agent] Entity extraction LLM failed: %s.", e)
        return []


def _resolve_pdf_path(path_str: str) -> str:
    """Resolve the PDF path by checking absolute, relative, and local fallbacks.

    Args:
        path_str: The raw path string from the payload.

    Returns:
        The verified absolute path to the PDF, or the original string if not found.
    """
    if not path_str:
        return ""

    # 1. Try path as is (works for absolute paths or CWD-relative)
    p = Path(path_str)
    if p.exists():
        return str(p.absolute())

    # 2. Try relative to the current working directory
    # (FastAPI usually starts at project root or phase3/)
    cwd_p = Path.cwd() / path_str
    if cwd_p.exists():
        return str(cwd_p.absolute())

    # 3. Try fallback inside phase3/data/uploads/
    # (Useful if payload only sends 'source.pdf')
    local_p = Path(__file__).parent.parent / "data" / "uploads" / Path(path_str).name
    if local_p.exists():
        logger.info(f"[Agent] Path fallback successful: {local_p}")
        return str(local_p.absolute())

    # 4. Try root data/uploads/ (if running from root)
    root_p = Path.cwd() / "phase3" / "data" / "uploads" / Path(path_str).name
    if root_p.exists():
        return str(root_p.absolute())

    logger.warning(f"[Agent] Could not resolve PDF path: {path_str}")
    return path_str


def process_images_vlm(
    image_blocks: list[dict[str, Any]],
    localized_pack: dict[str, Any],
    source_pdf_path: str,
) -> list[list[dict[str, Any]]]:
    """Process visual blocks using Qwen 2.5 VLM to identify substitutions.
    
    Args:
        image_blocks: A list of image block dictionaries from Phase 1.
        localized_pack: The localized text pack (nested pages format).
        source_pdf_path: Path to the original PDF.
        
    Returns:
        A list of processed Images respecting the Phase 3 output contract.
    """
    output_images = []
    
    # Resolve the path handle absolute/relative/fallback
    resolved_path = _resolve_pdf_path(source_pdf_path)
    logger.info(f"[Agent] Source PDF resolved to: {resolved_path}")

    # Map page texts for context
    # Handle both nested 'pages' format and flat list format
    page_texts: dict[int, str] = {}
    
    if isinstance(localized_pack, list):
        # Flat list format
        for block in localized_pack:
            pid = block.get("page_id", 0)
            text = block.get("localized_content", block.get("translated_content", block.get("text", "")))
            if text:
                if pid not in page_texts:
                    page_texts[pid] = []
                page_texts[pid].append(text)
    elif isinstance(localized_pack, dict) and "pages" in localized_pack:
        # Nested format
        for page in localized_pack.get("pages", []):
            pid = page.get("page_id", 0)
            lines = [b.get("localized_content", b.get("translated_content", b.get("text", ""))) for b in page.get("text_blocks", [])]
            if pid not in page_texts:
                page_texts[pid] = []
            page_texts[pid].extend([l for l in lines if l])
            
    # Join text blocks into one string per page
    for pid in page_texts:
        page_texts[pid] = " ".join(page_texts[pid])
        
    for block in image_blocks:
        image_index = block.get("image_index", 0)
        bbox = block.get("bbox", [0.0, 0.0, 0.0, 0.0])
        page_id = block.get("page_id", 0)
        
        # Build context from current page and previous page (if exists)
        ctx_parts = []
        if page_id - 1 in page_texts:
            ctx_parts.append(page_texts[page_id - 1])
        if page_id in page_texts:
            ctx_parts.append(page_texts[page_id])
            
        context = " ".join(ctx_parts)
        
        try:
            if not resolved_path or not os.path.exists(resolved_path):
                raise FileNotFoundError(f"Missing or invalid source_pdf_path: {resolved_path}")
            import fitz
            doc = fitz.open(resolved_path)
            # Default to extracting from the matching page_id
            # Assuming page_id is 1-indexed in our data
            page_idx = max(0, page_id - 1)
            pdf_page = doc[page_idx]
            rect = fitz.Rect(bbox)
            # Render the clipped rectangle
            pix = pdf_page.get_pixmap(clip=rect)
            # Convert to PNG, then Base64
            img_bytes = pix.tobytes("png")
            base64_img = base64.b64encode(img_bytes).decode("utf-8")
            
            # The prepared message layout for Qwen2.5-VL via OpenAI compatible API:
            user_messages = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_img}"}
                },
                {
                    "type": "text",
                    "text": f"Evaluate this image with context: '{context}'"
                }
            ]
            doc.close()
        except Exception as e:
            logger.warning("[Agent] Failed to read image from PDF: %s", e)
            base64_img = ""
            user_messages = [{"type": "text", "text": context}]
            
        # Call the VLM model if FPT API Key is available
        replacements = {}
        if _FPT_API_KEY:
            try:
                # Load VLM system prompt from file
                vlm_system_prompt = _read_prompt_file(_VLM_SYSTEM_PROMPT_PATH, "You are an expert Cultural Localization Assistant.")

                client = OpenAI(api_key=_FPT_API_KEY, base_url=_FPT_BASE_URL)
                response = client.chat.completions.create(
                    model=_FPT_VLM_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": vlm_system_prompt
                        },
                        {"role": "user", "content": user_messages},
                    ],
                    temperature=0.2,
                    max_tokens=1024,
                )
                raw_response = response.choices[0].message.content.strip()
                # Parse JSON if possible
                try:
                    # Strip out Markdown if exists
                    if raw_response.startswith("```json"):
                        raw_response = raw_response[7:-3].strip()
                    elif raw_response.startswith("```"):
                        raw_response = raw_response[3:-3].strip()
                    parsed = json.loads(raw_response)
                    if isinstance(parsed, dict):
                        # Flatten the nested visual format to just the english translation
                        flattened = {}
                        for k, v in parsed.items():
                            if k.startswith("visual:") and isinstance(v, dict) and "english_translation" in v:
                                flattened[k] = v["english_translation"]
                            else:
                                flattened[k] = v
                        replacements = flattened
                    else:
                        logger.warning("[Agent] VLM returned non-dict JSON: %s", raw_response)
                except json.JSONDecodeError:
                    logger.warning("[Agent] VLM returned non-JSON: %s", raw_response)
            except Exception as e:
                logger.warning("[Agent] VLM call failed: %s", e)
            
        # Final formatting for this image's output
        # Each image corresponds to a single dictionary in the resulting list
        # We ALWAYS append a record even if replacements are empty to ensure consistency
        output_images.append([
            {
                "page_id": page_id,
                "bbox": bbox,
                "image_index": image_index
            },
            {
                "replacements_json": replacements
            }
        ])
        
    logger.info(f"[Agent] Image processing complete. Extracted {len(output_images)} records.")
    return output_images


def rewrite_sentence_llm(
    vietnamese_sentence: str,
    english_entity: str,
    proposed_replacement: str,
    english_source: str = "",
) -> str:
    """Rewrite a Vietnamese sentence replacing a cultural entity using Gemma 4.

    Instead of naive string replacement (which fails because the entity
    name is English but the sentence is Vietnamese), this function sends
    the full Vietnamese sentence to the LLM and asks it to recreate the
    sentence with the cultural replacement naturally integrated.

    Args:
        vietnamese_sentence: The current Vietnamese sentence to rewrite.
        english_entity: The original English entity name (e.g., 'cottage').
        proposed_replacement: The Vietnamese cultural replacement (e.g., 'nhà tranh').
        english_source: The original English sentence for additional context.

    Returns:
        The rewritten Vietnamese sentence with the replacement applied.
        Returns the original sentence unchanged if the LLM call fails.
    """
    if not _FPT_API_KEY:
        logger.warning("[Agent] No FPT API key — skipping LLM rewrite.")
        return vietnamese_sentence

    system_prompt = _read_prompt_file(_REWRITE_PROMPT_PATH, _FALLBACK_REWRITE_PROMPT)

    user_prompt = (
        f"English source sentence: {english_source}\n"
        f"Old Vietnamese sentence (for reference only, create a fresh translation): {vietnamese_sentence}\n\n"
        f"Instructions:\n"
        f"- Translate the English source sentence into Vietnamese.\n"
        f"- Find the concept '{english_entity}' in the English source, and translate it as '{proposed_replacement}' instead of its literal translation.\n\n"
        f"Output ONLY the new translated Vietnamese sentence:"
    )

    try:
        client = OpenAI(api_key=_FPT_API_KEY, base_url=_FPT_BASE_URL)
        response = client.chat.completions.create(
            model=_FPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=512,
        )

        result = response.choices[0].message.content.strip()

        # Basic sanity: if the LLM returned something extremely short
        # or suspiciously different, fall back to the original.
        if len(result) < 3:
            logger.warning(
                "[Agent] LLM rewrite too short (%d chars), keeping original.",
                len(result),
            )
            return vietnamese_sentence

        # Strip any surrounding quotes the LLM may have added
        if (result.startswith('"') and result.endswith('"')) or \
           (result.startswith("'") and result.endswith("'")):
            result = result[1:-1]

        logger.info(
            "[Agent] Rewrote sentence: '%s' -> '%s'",
            vietnamese_sentence[:60],
            result[:60],
        )
        return result

    except Exception as e:
        logger.warning(
            "[Agent] LLM sentence rewrite failed: %s. Keeping original.", e
        )
        return vietnamese_sentence


def generate_proposals_fallback(
    entity_names: list[dict[str, str]],
    protected_names: list[str],
) -> list[LocalizationProposal]:
    """Generate proposals using deterministic rules (no LLM).

    Used when the FPT Marketplace API is unavailable or for testing.

    Args:
        entity_names: List of entity dicts from the text pack.
        protected_names: Names that must not be changed.

    Returns:
        A list of LocalizationProposal objects.
    """
    protected_lower = {n.lower() for n in protected_names}
    entity_lookup: dict[str, list[int]] = {}

    for e in entity_names:
        name = e["name"]
        if name not in entity_lookup:
            entity_lookup[name] = []
        for p in e.get("pages", []):
            if p not in entity_lookup[name]:
                entity_lookup[name].append(p)

    proposals: list[LocalizationProposal] = []
    counter = 0

    for fallback in _FALLBACK_PROPOSALS:
        original = fallback["original"]
        if original.lower() in protected_lower:
            continue
        if original not in entity_lookup:
            continue

        counter += 1
        proposals.append(LocalizationProposal(
            proposal_id=f"prop_fb_{counter:03d}",
            original=original,
            proposed=fallback["proposed"],
            affected_pages=entity_lookup[original],
            rationale=fallback["rationale"],
        ))

    return proposals


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_user_prompt(
    entity_names: list[dict[str, str]],
    qa_feedback: dict | None,
) -> str:
    """Build the user prompt for the LLM."""
    # Deduplicate entities
    unique: dict[str, dict] = {}
    for e in entity_names:
        name = e["name"]
        if name not in unique:
            unique[name] = {"name": name, "type": e["type"], "pages": []}
        for p in e.get("pages", []):
            if p not in unique[name]["pages"]:
                unique[name]["pages"].append(p)

    entity_list_str = json.dumps(
        list(unique.values()), indent=2, ensure_ascii=False
    )

    prompt = (
        f"Here are the cultural entities found in a Vietnamese children's book "
        f"Propose Vietnamese replacements for entities "
        f"that are culturally unfamiliar to Vietnamese children.\n\n"
        "The contain need to be as familar as possible to Vietnamese culture.\n"
        "The meaning of the content can be changed to match the culture of Vietnamese.\n"
        "Vietnamese words could be changed into another vietnamese word.\n"
        f"Entities:\n{entity_list_str}"
    )

    if qa_feedback:
        prompt += (
            f"\n\nIMPORTANT: This is a re-run after QA rejected previous output. "
            f"QA feedback:\n{json.dumps(qa_feedback, indent=2, ensure_ascii=False)}\n"
            f"Please adjust your proposals to address the QA issues."
        )

    return prompt


def _parse_llm_response(
    raw: str,
    entity_names: list[dict[str, str]],
    protected_names: list[str],
) -> list[LocalizationProposal]:
    """Parse the LLM's JSON response into LocalizationProposal objects.

    Args:
        raw: The raw LLM response string (expected JSON array).
        entity_names: Original entity list for page lookup.
        protected_names: Protected names to filter out.

    Returns:
        Parsed list of LocalizationProposal objects.
    """
    protected_lower = {n.lower() for n in protected_names}

    # Strip markdown fences if the model wraps them
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        items = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("[Agent] Failed to parse LLM JSON. Raw: %s", raw[:200])
        return []

    if not isinstance(items, list):
        return []

    # Build page lookup
    page_lookup: dict[str, list[int]] = {}
    for e in entity_names:
        name = e["name"]
        if name not in page_lookup:
            page_lookup[name] = []
        for p in e.get("pages", []):
            if p not in page_lookup[name]:
                page_lookup[name].append(p)

    proposals: list[LocalizationProposal] = []
    for i, item in enumerate(items):
        original = item.get("original", "")
        proposed = item.get("proposed", "")
        rationale = item.get("rationale", "LLM-generated proposal")

        # Skip invalid or protected
        if not original or not proposed:
            continue
        if original.lower() in protected_lower:
            continue
        if original == proposed:
            continue

        pages = page_lookup.get(original, [1])

        proposals.append(LocalizationProposal(
            proposal_id=f"prop_llm_{i + 1:03d}",
            original=original,
            proposed=proposed,
            affected_pages=pages,
            rationale=rationale,
        ))

    return proposals
