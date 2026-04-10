"""
Task #p2.3: Reviser Agent — AI quality assessment for translations.

Calls Gemini with a different prompt to evaluate translation quality,
scoring from 1-10 and providing reasons for deductions. Checks
compliance with global metadata constraints.
"""

import json
import logging
import os
import time

from google import genai

from phase2.models import RevisionResult

logger = logging.getLogger(__name__)

# Model selection — configurable via env var, defaults to flash for free tier
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Rate limit retry configuration
API_MAX_RETRIES = 5
API_BASE_DELAY = 5.0


def _build_reviser_system_prompt(global_metadata: dict) -> str:
    """Builds the system prompt for the Reviser Agent.

    Configures the LLM to act as a translation quality reviewer,
    checking fidelity, constraint compliance, and naturalness.

    Args:
        global_metadata: The global metadata dictionary containing
            all constraint groups.

    Returns:
        str: A formatted system prompt for the Reviser Agent.
    """
    ip_params = global_metadata.get("ip_brand_parameters", {})
    editorial_params = global_metadata.get("editorial_parameters", {})
    content_params = global_metadata.get("content_parameters", {})

    protected_names = ip_params.get("protected_names", [])
    style_register = editorial_params.get("style_register", "general")
    fidelity = content_params.get("translation_fidelity", "Strict")

    return f"""You are a professional translation quality reviewer specializing in children's books.
Your task is to evaluate translations for accuracy, naturalness, and compliance with project rules.

EVALUATION CRITERIA:
1. Fidelity to source text (fidelity mode: {fidelity})
2. Protected names MUST remain untranslated: {json.dumps(protected_names)}
3. Language must be appropriate for: {style_register}
4. No plot alterations or content additions/removals
5. Natural-sounding target language
6. Consistent tone and register

SCORING GUIDE:
- 9-10: Excellent — accurate, natural, fully compliant
- 7-8: Good — minor issues but acceptable
- 5-6: Fair — noticeable errors or constraint violations
- 3-4: Poor — significant accuracy or compliance issues
- 1-2: Unacceptable — major errors or multiple violations

OUTPUT FORMAT:
Return ONLY a JSON object with exactly these fields:
{{"score": <number 1-10>, "reason": "<brief explanation if score < 8, empty string if score >= 8>"}}

Do NOT include any other text, markdown, or explanation outside the JSON."""


def _build_reviser_user_prompt(
    original_texts: list[str],
    translated_texts: list[str],
) -> str:
    """Builds the user prompt for the Reviser Agent.

    Presents the original and translated texts side-by-side for evaluation.

    Args:
        original_texts: List of source language texts.
        translated_texts: List of translated texts to evaluate.

    Returns:
        str: A formatted user prompt for the LLM.
    """
    pairs = []
    for i, (orig, trans) in enumerate(zip(original_texts, translated_texts)):
        pairs.append(f"Block {i + 1}:\n  Original: {orig}\n  Translation: {trans}")

    return (
        "Evaluate the following translations. "
        "Score from 1 to 10 and explain any issues.\n\n"
        + "\n\n".join(pairs)
    )


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
                    temperature=0.2,
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


def revise_translation(
    original_texts: list[str],
    translated_texts: list[str],
    global_metadata: dict,
    api_key: str,
) -> RevisionResult:
    """Evaluates a batch of translations using Gemini API.

    Sends the original texts and their translations to the Reviser Agent,
    which scores the translation quality and provides feedback.

    Args:
        original_texts: List of source language texts.
        translated_texts: List of translated target texts.
        global_metadata: Global metadata constraints dictionary.
        api_key: Gemini API key for authentication.

    Returns:
        RevisionResult: Contains a score (1-10) and a reason string.

    Raises:
        google.genai.errors.APIError: If the API call fails.
    """
    client = genai.Client(api_key=api_key)

    system_prompt = _build_reviser_system_prompt(global_metadata)
    user_prompt = _build_reviser_user_prompt(original_texts, translated_texts)

    response_text = _call_api_with_retry(client, system_prompt, user_prompt)

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        response_text = "\n".join(lines).strip()

    try:
        result = json.loads(response_text)
        return RevisionResult(
            score=float(result.get("score", 0)),
            reason=result.get("reason", ""),
        )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error(
            "Failed to parse reviser response: %s\nRaw: %s",
            e,
            response_text,
        )
        # Default to a cautious low score to trigger retry
        return RevisionResult(
            score=5.0,
            reason=f"Could not parse reviser output: {response_text[:200]}",
        )
