"""
Task #p1.1: Intelligent Metadata Extraction

Uses Gemini 2.5 Structured Outputs to parse an unstructured project brief
into a standardized GlobalMetadata schema model, discarding irrelevant parameters.
"""

import logging
import os

from google import genai

from phase1.models import GlobalMetadata

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def extract_metadata_from_brief(raw_brief_text: str, api_key: str) -> GlobalMetadata:
    """Extracts structured GlobalMetadata from raw project brief text.
    
    Acts as a Publisher PM parsing the incoming email/doc from the client
    and mapping it precisely to our allowed schema. Any constraints found
    in the raw text that DO NOT map to GlobalMetadata parameters will
    simply be ignored.

    Args:
        raw_brief_text: Raw string containing instructions.
        api_key: Gemini API Key for authentication.

    Returns:
        GlobalMetadata: Populated Pydantic object.
        
    Raises:
        google.genai.errors.APIError: If the API call fails.
        Exception: If parsing schema fails.
    """
    client = genai.Client(api_key=api_key)

    system_instruction = (
        "You are an expert Project Manager reading an unstructured project brief "
        "for a children's book localization project. Your job is to extract the rules "
        "and parameters requested by the client into the STRICT JSON schema provided.\n\n"
        "RULES:\n"
        "1. Extract ONLY the parameters that fit the provided schema.\n"
        "2. Any extra rules requested by the client that are not in the schema should be IGNORED.\n"
        "3. Interpret their language correctly into boolean flags where required.\n"
        "4. Output must perfectly match the schema definitions."
    )

    def _strip_defaults(schema_dict: dict) -> dict:
        """Recursively removes 'default' keys from a JSON schema dictionary."""
        if isinstance(schema_dict, dict):
            return {k: _strip_defaults(v) for k, v in schema_dict.items() if k != "default"}
        elif isinstance(schema_dict, list):
            return [_strip_defaults(item) for item in schema_dict]
        return schema_dict

    def _call_api_with_retry() -> str:
        """Calls the Gemini API with exponential backoff for rate limit errors.
        
        Returns:
            str: The JSON response text from the API.
            
        Raises:
            RuntimeError: If all retries are exhausted.
        """
        for attempt in range(5):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=raw_brief_text,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=clean_schema,
                    ),
                )
                return response.text
            except Exception as e:
                import time
                error_str = str(e)
                if any(code in error_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    delay = 5.0 * (2 ** attempt)
                    logger.warning(
                        "Rate limited (attempt %d/%d). Retrying in %.1f seconds...",
                        attempt + 1, 5, delay
                    )
                    time.sleep(delay)
                else:
                    raise
        raise RuntimeError("Gemini API rate limit exceeded after 5 retries")

    try:
        # Generate raw JSON schema and strip defaults
        raw_schema = GlobalMetadata.model_json_schema()
        clean_schema = _strip_defaults(raw_schema)

        response_text = _call_api_with_retry()

        # Output should be valid JSON mapped against GlobalMetadata
        return GlobalMetadata.model_validate_json(response_text)

    except Exception as e:
        logger.error(f"Failed to extract metadata: {e}")
        raise
