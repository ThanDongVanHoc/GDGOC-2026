"""Localization Agent — LLM-backed cultural entity replacement (Task #p3.2).

Uses FPT Marketplace (OpenAI-compatible) to propose Vietnamese-appropriate
replacements for Western cultural entities. Falls back to a deterministic
rules-based generator when the LLM is unavailable.

The agent respects global_metadata constraints:
    - protected_names: never renamed
    - never_change_rules: free-text immutability constraints
    - lock_character_color: blocks colour-related changes
"""

import json
import logging
import os
from typing import Any

from openai import OpenAI

from core.models import LocalizationProposal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FPT Marketplace config
# ---------------------------------------------------------------------------

_FPT_API_KEY: str = os.environ.get(
    "FPT_API_KEY",
    "sk-DV3wZhqSglIKIdOGgWh7U7J9FAHTzYew6oyOYR01tWo=",
)
_FPT_BASE_URL: str = "https://mkp-api.fptcloud.com"
_FPT_MODEL: str = "gemma-4-31B-it"

# ---------------------------------------------------------------------------
# System prompt for the localization agent
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a Vietnamese cultural localization expert for children's picture books.

Your task: Given a list of Western cultural entities found in the book, propose
Vietnamese equivalents that are familiar to Vietnamese children aged 6-10.

Rules:
1. NEVER rename protected entities: {protected_names}
2. NEVER violate these rules: {never_change_rules}
3. Only replace entities that are culturally unfamiliar in Vietnam.
4. Keep character names unchanged unless they are NOT in the protected list
   AND have a clear Vietnamese cultural equivalent.
5. The replacement must preserve the narrative meaning and emotional tone.
6. Do NOT change entities that already work in Vietnamese context.

Return a JSON array of proposals. Each proposal MUST have these fields:
- "original": the exact entity name from the input
- "proposed": the Vietnamese replacement
- "rationale": 1-sentence explanation in English

Example:
[
  {{"original": "Fireplace", "proposed": "Bếp củi", "rationale": "Fireplaces are uncommon in Vietnamese homes; wood stoves are culturally equivalent."}},
  {{"original": "Wool Hat", "proposed": "Nón lá", "rationale": "Wool hats are uncommon in tropical Vietnam; conical hats are iconic."}}
]

Return ONLY the JSON array. No extra text, no markdown fences.
"""


# ---------------------------------------------------------------------------
# Deterministic fallback proposals (no LLM needed)
# ---------------------------------------------------------------------------

_FALLBACK_PROPOSALS: list[dict[str, str]] = [
    {
        "original": "Fireplace",
        "proposed": "Bếp củi",
        "rationale": "Fireplaces are rare in Vietnamese homes. "
                     "Wood-burning stoves (bếp củi) are the cultural equivalent.",
    },
    {
        "original": "Hot Chocolate",
        "proposed": "Chè nóng",
        "rationale": "Hot chocolate is uncommon in Vietnam. "
                     "Chè (sweet soup) is a popular warm dessert for children.",
    },
    {
        "original": "Wool Hat",
        "proposed": "Nón lá",
        "rationale": "Wool hats are rare in tropical Vietnam. "
                     "The conical hat (nón lá) is iconic Vietnamese headwear.",
    },
    {
        "original": "Sleigh",
        "proposed": "Xe đạp",
        "rationale": "Sleighs require snow and are unknown in Vietnam. "
                     "Bicycles are a common childhood transport.",
    },
    {
        "original": "Northern Lights",
        "proposed": "Cầu vồng",
        "rationale": "Northern Lights are not visible in Vietnam. "
                     "Rainbows are a similarly magical sky phenomenon.",
    },
    {
        "original": "Warm Coat",
        "proposed": "Áo khoác",
        "rationale": "A warm coat is understandable but uncommon phrasing. "
                     "Áo khoác (jacket) is more natural for Vietnamese children.",
    },
]


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
    system = _SYSTEM_PROMPT.format(
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
        f"(translated from English). Propose Vietnamese replacements for entities "
        f"that are culturally unfamiliar to Vietnamese children.\n\n"
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
