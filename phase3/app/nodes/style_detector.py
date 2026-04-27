import asyncio
import logging
from typing import Any
from app.state import Phase3State
from app.prompt_builder import build_style_detection_prompt

logger = logging.getLogger(__name__)

# Model for style detection
_DETECTION_MODEL = "gemma-4-31B-it"

async def detect_style_node(state: Phase3State) -> Phase3State:
    """LLM-based style detection node.
    
    Analyzes a sample of the text pack to determine the most appropriate
    style_register if it's currently generic or missing.
    """
    metadata = state["global_metadata"]
    current_style = getattr(metadata, "style_register", "general")
    
    # If a specific style is already set (and not general), we respect it.
    # We only auto-detect if it's "general" or empty.
    if current_style and current_style != "general":
        logger.info(f"Style already set to '{current_style}', skipping detection.")
        return state

    client = state.get("client")
    if not client:
        logger.warning("[Phase3:StyleDetector] Client is None. Skipping detection.")
        return state

    blocks = state.get("blocks", [])
    if not blocks:
        return state

    # Take a sample of the first few blocks for analysis
    sample_size = min(len(blocks), 50)
    sample_text = "\n".join([b["english_content"] for b in blocks[:sample_size]])
    
    if not sample_text.strip():
        logger.warning("Empty sample text for style detection. Defaulting to 'general'.")
        return state

    logger.info(f"Detecting style for {len(blocks)} blocks...")
    
    system_msg = build_style_detection_prompt()
    client = state["client"]

    try:
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model=_DETECTION_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Text Sample:\n\n{sample_text}"},
            ],
            temperature=0.0,  # Deterministic for classification
            max_tokens=20,
        )
        detected_style = resp.choices[0].message.content.strip().lower()
        
        # Validate detected style against supported list
        supported_styles = ["children_book", "manga", "novel", "academic", "general"]
        if detected_style in supported_styles:
            logger.info(f"Detected style: '{detected_style}'")
            # Update global metadata in state
            metadata.style_register = detected_style
        else:
            logger.warning(f"LLM returned unsupported style '{detected_style}'. Falling back to 'general'.")
            metadata.style_register = "general"

    except Exception as e:
        logger.error(f"Style detection failed: {e}. Falling back to 'general'.")
        metadata.style_register = "general"

    return {**state, "global_metadata": metadata}
