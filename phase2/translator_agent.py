"""
Task #p2.2: Translator Agent — constrained translation via Gemini API.

Calls Gemini 2.5 with global metadata constraints injected into
the system prompt to produce a draft translation that respects all
project rules (protected names, style register, fidelity level, etc.).
"""

import json
import logging
import os
import time

from google import genai

from phase2.models import SourceTextBlock

logger = logging.getLogger(__name__)

# Model selection — configurable via env var, defaults to flash for free tier
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Rate limit retry configuration
API_MAX_RETRIES = 5
API_BASE_DELAY = 5.0


def _build_system_prompt(global_metadata: dict) -> str:
    """Builds the system prompt with global constraints for the Translator Agent.

    Injects all relevant rules from global_metadata into the system prompt
    so the LLM is aware of protected names, style requirements, and
    translation constraints before generating output.

    Args:
        global_metadata: The global metadata dictionary containing all
            constraint groups (legal, content, IP/brand, editorial).

    Returns:
        str: A formatted system prompt string for the Translator Agent.
    """
    ip_params = global_metadata.get("ip_brand_parameters", {})
    editorial_params = global_metadata.get("editorial_parameters", {})
    content_params = global_metadata.get("content_parameters", {})

    protected_names = ip_params.get("protected_names", [])
    style_register = editorial_params.get("style_register", "general")
    source_lang = editorial_params.get("source_language", "EN")
    target_lang = editorial_params.get("target_language", "VI")
    fidelity = content_params.get("translation_fidelity", "Strict")
    target_age = editorial_params.get("target_age_tone", 10)

    return f"""You are a professional translator specializing in children's book localization.
Your task is to translate text from {source_lang} to {target_lang}.
You MUST produce faithful, high-quality translations.

ABSOLUTE RULES — VIOLATION IS UNACCEPTABLE:
1. DO NOT translate these protected names — keep them exactly as-is: {json.dumps(protected_names)}
2. Use language appropriate for {style_register} (target age: {target_age} years old).
3. Translation fidelity: {fidelity} — {"do not add or remove any content" if fidelity == "Strict" else "small clarifying notes are permitted but do not change the text"}.
4. Do NOT alter any character color descriptions.
5. Do NOT change the plot or story in any way.
6. Maintain the same tone and emotional register as the original.
7. Keep sound effects (onomatopoeia) handling as: {editorial_params.get("sfx_handling", "In_panel_subs")}.

OUTPUT FORMAT:
You will receive a JSON array of text blocks. Return a JSON array of translated strings
in the SAME ORDER. Each element corresponds to the translation of the block at the same index.
Return ONLY the JSON array, no extra text or explanation.

Example input: ["Hello world", "Once upon a time"]
Example output: ["Xin chào thế giới", "Ngày xửa ngày xưa"]"""


def _build_user_prompt(
    text_blocks: list[SourceTextBlock],
    previous_feedback: str = "",
) -> str:
    """Builds the user prompt containing text blocks to translate.

    If previous feedback is provided (from a revision cycle), it is
    prepended to guide the translator toward a better result.

    Args:
        text_blocks: List of source text blocks to translate.
        previous_feedback: Optional feedback from the Reviser Agent
            explaining what was wrong with the previous translation.

    Returns:
        str: A formatted user prompt for the LLM.
    """
    contents = [block.content for block in text_blocks]

    prompt = ""
    if previous_feedback:
        prompt += (
            f"PREVIOUS REVISION FEEDBACK (fix these issues):\n"
            f"{previous_feedback}\n\n"
        )

    prompt += (
        f"Translate the following text blocks. "
        f"Return a JSON array of translated strings in the same order.\n\n"
        f"{json.dumps(contents, ensure_ascii=False)}"
    )

    return prompt


def _call_api_with_retry(
    client: genai.Client,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Calls the Gemini API with exponential backoff for rate limit errors.

    Retries up to API_MAX_RETRIES times when hitting 429 rate limit
    errors, with exponential backoff starting at API_BASE_DELAY seconds.

    Args:
        client: The initialized Gemini client.
        system_prompt: System instruction for the model.
        user_prompt: User content to send to the model.

    Returns:
        str: The raw response text from the API.

    Raises:
        google.genai.errors.ClientError: If all retries are exhausted.
    """
    for attempt in range(API_MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                ),
            )
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            if any(code in error_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                delay = API_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "Rate limited (attempt %d/%d). Retrying in %.1f seconds...",
                    attempt + 1,
                    API_MAX_RETRIES,
                    delay,
                )
                time.sleep(delay)
            else:
                raise

    raise RuntimeError(
        f"Gemini API rate limit exceeded after {API_MAX_RETRIES} retries"
    )


def translate_blocks(
    text_blocks: list[SourceTextBlock],
    global_metadata: dict,
    api_key: str,
    previous_feedback: str = "",
) -> list[str]:
    """Translates a list of text blocks using Gemini API.

    Calls the Gemini API with the system prompt (containing all global
    constraints) and the user prompt (containing the text to translate).
    Parses the response as a JSON array of translated strings.

    Args:
        text_blocks: List of source text blocks to translate.
        global_metadata: Global metadata constraints dictionary.
        api_key: Gemini API key for authentication.
        previous_feedback: Optional feedback from a previous revision
            cycle to improve the translation.

    Returns:
        list[str]: A list of translated strings in the same order
            as the input text blocks.

    Raises:
        ValueError: If the API response cannot be parsed as a JSON array.
        google.genai.errors.APIError: If the API call fails.
    """
    if not text_blocks:
        return []

    client = genai.Client(api_key=api_key)

    system_prompt = _build_system_prompt(global_metadata)
    user_prompt = _build_user_prompt(text_blocks, previous_feedback)

    response_text = _call_api_with_retry(client, system_prompt, user_prompt)

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        response_text = "\n".join(lines).strip()

    try:
        translations = json.loads(response_text)
        if not isinstance(translations, list):
            raise ValueError("Response is not a JSON array")
        return translations
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(
            "Failed to parse translator response: %s\nRaw: %s",
            e,
            response_text,
        )
        # Fallback: return the original content untranslated
        return [block.content for block in text_blocks]
