"""
Step 3: Text Replacement — Remove old text and render new Vietnamese text.

This is a HYBRID step (Code + minimal AI):
  1. For each text region:
     a. Create a mask from the bbox
     b. Inpaint to erase old text (cv2.inpaint — fast, no AI needed for MVP)
     c. Detect font properties (color, size) from the original region
     d. Render new Vietnamese text using PIL with matched properties
     e. Composite the new text onto the image

This step does NOT use diffusion models for text rendering since they
cannot accurately render Vietnamese diacritics.
"""

import io
import logging

import cv2
import numpy as np
from PIL import Image

from models.schemas import TextReplacement
from services.text_renderer import render_text_on_region, detect_text_properties

logger = logging.getLogger(__name__)


def _bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes to OpenCV BGR array."""
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image bytes.")
    return img


def _cv2_to_bytes(img: np.ndarray, fmt: str = ".png") -> bytes:
    """Convert OpenCV BGR array to PNG bytes."""
    success, encoded = cv2.imencode(fmt, img)
    if not success:
        raise ValueError("Failed to encode image.")
    return encoded.tobytes()


def _create_text_mask(
    img_shape: tuple[int, int, int],
    bbox: list[int],
    padding: int = 2,
) -> np.ndarray:
    """Create a binary mask for the text region (white = text area)."""
    h, w = img_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    x1, y1, x2, y2 = bbox
    # Clamp to image bounds with padding
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(w, x2 + padding)
    y2 = min(h, y2 + padding)
    mask[y1:y2, x1:x2] = 255
    return mask


def _inpaint_text_region(
    img: np.ndarray,
    mask: np.ndarray,
    inpaint_radius: int = 5,
) -> np.ndarray:
    """Erase text by inpainting the masked region.

    Uses cv2.INPAINT_TELEA for the MVP — fast and decent quality.
    Can be replaced with LaMa for better results later.
    """
    return cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)


async def run_text_replacement(
    image_bytes: bytes,
    texts: list[TextReplacement],
) -> bytes:
    """Replace text regions with new Vietnamese text.

    Args:
        image_bytes: Current image as bytes.
        texts: List of text replacements with bbox and new text.

    Returns:
        Updated image bytes with Vietnamese text rendered.
    """
    if not texts:
        logger.info("[Text Replacement] No text replacements — skipping.")
        return image_bytes

    img = _bytes_to_cv2(image_bytes)
    original_img = img.copy()

    logger.info(f"[Text Replacement] Replacing {len(texts)} text region(s).")

    for i, text_item in enumerate(texts):
        x1, y1, x2, y2 = text_item.bbox
        logger.info(
            f"[Text Replacement] Text {i + 1}/{len(texts)}: "
            f"'{text_item.original_text}' → '{text_item.new_text}' "
            f"at [{x1}, {y1}, {x2}, {y2}]"
        )

        # 3a. Detect font properties from original region
        props = detect_text_properties(
            original_img, text_item.bbox,
            override_size=text_item.font_size,
            override_color=text_item.font_color,
        )
        logger.info(f"  Detected properties: {props}")

        # 3b. Create mask and inpaint to erase old text
        mask = _create_text_mask(img.shape, text_item.bbox, padding=3)
        img = _inpaint_text_region(img, mask, inpaint_radius=7)

        # 3c. Render new text onto the inpainted region
        img = render_text_on_region(
            img=img,
            bbox=text_item.bbox,
            text=text_item.new_text,
            font_size=props["font_size"],
            font_color=props["font_color"],
        )

        logger.info(f"[Text Replacement] Text {i + 1}/{len(texts)} replaced successfully.")

    return _cv2_to_bytes(img)
