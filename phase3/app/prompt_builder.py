"""Dynamic prompt builder for Phase 3 localization.

Generates style-aware system prompts for both the cultural scoring and
cascading translation nodes based on ``global_metadata.style_register``
and related metadata fields.
"""

from core.models import GlobalMetadata

# ---------------------------------------------------------------------------
# Style register → localization instruction map
# ---------------------------------------------------------------------------

_LOCALIZATION_STYLE_MAP: dict[str, str] = {
    "children_book": (
        "You are an expert Vietnamese cultural localizer for children's picture books.\n"
        "- MANDATORY: Replace Western cultural objects with Vietnamese equivalents (e.g., 'snowman' -> 'chú Tễu').\n"
        "- Treat 'raw_translation' as ONLY a hint; prioritize re-localizing 'english' content.\n"
        "- Use playful, simple vocabulary for young readers.\n"
    ),
    "manga": (
        "You are an expert Vietnamese cultural localizer for manga and comics.\n"
        "- Maintain energetic, punchy dialogue with light Vietnamese slang where natural.\n"
        "- Preserve sound effects (onomatopoeia) in their original form or provide "
        "a Vietnamese phonetic equivalent in parentheses.\n"
        "- Cultural swaps should feel natural in a Vietnamese urban/school setting.\n"
        "- Keep character speech patterns distinct and expressive.\n"
    ),
    "novel": (
        "You are an expert Vietnamese cultural localizer for literary novels.\n"
        "- Use a nuanced, literary Vietnamese register with rich vocabulary.\n"
        "- Prioritize narrative flow and emotional resonance over literal fidelity.\n"
        "- Cultural localization should be subtle — replace only elements that "
        "would feel alien to a Vietnamese reader, keeping universal elements intact.\n"
        "- Maintain the author's stylistic voice (e.g., terse prose stays terse).\n"
    ),
    "academic": (
        "You are a precise Vietnamese technical/academic localizer.\n"
        "- Use formal, precise Vietnamese with correct technical terminology.\n"
        "- Minimize cultural localization — keep references factual and accurate.\n"
        "- Preserve all proper nouns, citations, and technical terms unless a "
        "widely-accepted Vietnamese equivalent exists.\n"
        "- Prioritize clarity and precision over stylistic flair.\n"
    ),
    "general": (
        "You are an expert Vietnamese cultural localizer.\n"
        "- Use a balanced, neutral Vietnamese register suitable for a broad audience.\n"
        "- Replace Western cultural objects with Vietnamese equivalents when the "
        "swap improves relatability without distorting meaning.\n"
        "- Maintain a natural conversational tone.\n"
    ),
}

# ---------------------------------------------------------------------------
# Style register → few-shot examples
# ---------------------------------------------------------------------------

_FEW_SHOTS: dict[str, str] = {
    "children_book": (
        "EXAMPLES OF AGGRESSIVE LOCALIZATION:\n"
        "- English: 'They built a big snowman.' -> Localized: 'Chúng em cùng nhau nặn một chú Tễu bằng đất sét thật to.'\n"
        "- English: 'The Easter Bunny left eggs.' -> Localized: 'Chú Cuội đã để lại những món quà bất ngờ.'\n"
        "- English: 'We ate turkey for Thanksgiving.' -> Localized: 'Cả nhà cùng quây quần bên mâm cơm tất niên dưa hành bánh chưng.'\n"
    ),
    "manga": (
        "EXAMPLES OF AGGRESSIVE LOCALIZATION:\n"
        "- English: 'It's time for the Cultural Festival!' -> Localized: 'Đến lúc chuẩn bị cho Hội trại 26/3 rồi!'\n"
        "- English: 'I brought you a bento.' -> Localized: 'Tớ có mang cơm nắm cho cậu này.'\n"
        "- English: 'Senpai, wait up!' -> Localized: 'Anh gì ơi, đợi em với!'\n"
    ),
    "novel": (
        "EXAMPLES OF SUBTLE LOCALIZATION:\n"
        "- English: 'He felt as cold as a blizzard in Maine.' -> Localized: 'Anh cảm thấy cái lạnh thấu xương như những ngày đông miền Bắc.'\n"
        "- English: 'A pint of ale by the fireplace.' -> Localized: 'Một chén rượu nồng bên bếp lửa hồng.'\n"
    ),
}

# ---------------------------------------------------------------------------
# Style register → scoring instruction map
# ---------------------------------------------------------------------------

_SCORING_STYLE_MAP: dict[str, str] = {
    "children_book": (
        "Focus on elements that Vietnamese children aged 6-10 would find unfamiliar: "
        "Western holidays (Christmas, Halloween), cold-climate activities (skiing, "
        "snowball fights), Western foods (turkey, pumpkin pie), and Western folklore "
        "(tooth fairy, Easter bunny). Score these HIGH (7-10).\n"
        "Common universal objects (sun, rain, dog, cat) score LOW (0-2).\n"
    ),
    "manga": (
        "Focus on Japanese cultural elements that need Vietnamese adaptation: "
        "school customs (shoe lockers, bento boxes, cultural festivals), honorifics, "
        "seasonal references (cherry blossoms, Golden Week), and food (onigiri, "
        "takoyaki). Score these MEDIUM-HIGH (5-8) since manga readers may be "
        "familiar with some Japanese tropes.\n"
        "Universal action/emotion vocabulary scores LOW (0-2).\n"
    ),
    "novel": (
        "Focus on deep cultural references that affect narrative comprehension: "
        "social customs, historical allusions, idiomatic expressions, and culturally "
        "specific metaphors. Score proportionally to how much the reference would "
        "confuse a Vietnamese reader unfamiliar with the source culture.\n"
        "Generic descriptive prose scores LOW (0-2).\n"
    ),
    "academic": (
        "Focus only on culturally specific examples or case studies that "
        "reference a particular country's systems (legal frameworks, educational "
        "structures, measurement units). Score these MEDIUM (4-6).\n"
        "Technical terminology and universal scientific concepts score VERY LOW (0-1).\n"
    ),
    "general": (
        "Evaluate each text block on how much 'Cultural Context' or 'Cultural "
        "Anchors' it contains (e.g., specific weather, holidays, foods, folklore "
        "entities, idioms).\n"
        "0 = Generic text. 10 = Heavy cultural context.\n"
    ),
}


def build_localization_system_prompt(metadata: GlobalMetadata) -> str:
    """Build a style-aware system prompt for the cascading translation node.

    Composes the final prompt from four layers:
    1. Style-specific role and tone instructions.
    2. Age/complexity calibration from ``target_age_tone``.
    3. Hard constraints (protected names, never-change rules).
    4. Output format specification.

    Args:
        metadata: Validated global metadata containing style_register,
            target_age_tone, protected_names, and never_change_rules.

    Returns:
        A complete system prompt string ready for the LLM.
    """
    style = metadata.style_register or "general"
    base_instruction = _LOCALIZATION_STYLE_MAP.get(
        style, _LOCALIZATION_STYLE_MAP["general"]
    )

    # --- Age / complexity calibration ---
    age = metadata.target_age_tone
    if age <= 8:
        age_instruction = (
            "- Target audience: very young children (under 8). Use the simplest "
            "possible words and very short sentences.\n"
        )
    elif age <= 12:
        age_instruction = (
            "- Target audience: children aged 8-12. Use clear, engaging language "
            "with moderate vocabulary.\n"
        )
    elif age <= 16:
        age_instruction = (
            "- Target audience: young adults (13-16). Natural conversational "
            "Vietnamese is appropriate; moderate complexity.\n"
        )
    else:
        age_instruction = (
            "- Target audience: adults (16+). Full Vietnamese vocabulary and "
            "complex sentence structures are acceptable.\n"
        )

    # --- Hard constraints ---
    constraints: list[str] = []
    if metadata.protected_names:
        names_str = ", ".join(f"'{n}'" for n in metadata.protected_names)
        constraints.append(
            f"- NEVER rename these protected entities: {names_str}.\n"
        )
    if metadata.never_change_rules:
        for rule in metadata.never_change_rules:
            constraints.append(f"- NEVER violate: {rule}\n")
    if not metadata.cultural_localization:
        constraints.append(
            "- Cultural localization is DISABLED. Translate faithfully without "
            "swapping cultural objects.\n"
        )

    constraint_block = "".join(constraints) if constraints else ""

    # --- Consistency instruction ---
    consistency = (
        "- Respect 'Context of previously localized parts' for consistency.\n"
    )

    # --- Output format ---
    output_format = (
        'Output EXACTLY a JSON array: '
        '[{"id": <id>, "localization": "<translated_text>"}]'
    )

    few_shots = _FEW_SHOTS.get(style, "")
    if few_shots:
        few_shots = f"\n{few_shots}\n"

    return (
        f"{base_instruction}"
        f"{age_instruction}"
        f"{constraint_block}"
        f"{consistency}"
        f"{few_shots}"
        f"{output_format}"
    )


def build_scoring_system_prompt(metadata: GlobalMetadata) -> str:
    """Build a style-aware system prompt for the cultural scoring node.

    Args:
        metadata: Validated global metadata containing style_register.

    Returns:
        A complete system prompt string for the cultural density scorer.
    """
    style = metadata.style_register or "general"
    style_guidance = _SCORING_STYLE_MAP.get(
        style, _SCORING_STYLE_MAP["general"]
    )

    return (
        "You are a cultural evaluator. Rate each text block on a scale of "
        "0 to 10 based on how much cultural adaptation it requires for a "
        "Vietnamese audience.\n"
        f"{style_guidance}"
        'Output EXACTLY a JSON array of objects: '
        '[{"id": 0, "score": 5}]'
    )


def build_style_detection_prompt() -> str:
    """Build a system prompt for the style detection node.

    Returns:
        A system prompt for style-register classification.
    """
    return (
        "Analyze the text sample and categorize it into exactly one of these styles:\n"
        "- children_book: Simple vocabulary, playful tone, children's story.\n"
        "- manga: Energetic, onomatopoeia, conversational, often comic/manga tropes.\n"
        "- novel: Literary, descriptive, nuanced prose.\n"
        "- academic: Formal, technical, precise.\n"
        "- general: Neutral, standard content.\n\n"
        "Output ONLY the category name."
    )
