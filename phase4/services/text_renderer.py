"""
Text Renderer — PIL-based Vietnamese text rendering service.

Handles:
  - Auto-detecting font properties (size, color) from original text region
  - Rendering Vietnamese text (with full diacritics support) onto images
  - Fitting text within a bounding box
"""

import logging
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# ── Font Configuration ──────────────────────────────────────────────────────

# Directory containing font files
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")

# Default font path — a Vietnamese-compatible font
# Priority: custom font in fonts/ dir → system DejaVuSans → PIL default
_FONT_PATHS = [
    os.path.join(FONTS_DIR, "NotoSans-Regular.ttf"),
    os.path.join(FONTS_DIR, "Roboto-Regular.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
]


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Get a Vietnamese-compatible font at the specified size."""
    for path in _FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    logger.warning("No TrueType font found — falling back to PIL default. "
                   "Vietnamese diacritics may not render correctly.")
    return ImageFont.load_default()


# ── Font Property Detection ─────────────────────────────────────────────────

def _hex_to_bgr(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to BGR tuple."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (b, g, r)


def _bgr_to_rgb(bgr: tuple[int, int, int]) -> tuple[int, int, int]:
    """Convert BGR to RGB tuple."""
    return (bgr[2], bgr[1], bgr[0])


def detect_text_properties(
    img: np.ndarray,
    bbox: list[int],
    override_size: int | None = None,
    override_color: str | None = None,
) -> dict:
    """Detect font properties from the original text region.

    Strategy:
      - Font size: estimated from bbox height (roughly 70% of region height)
      - Font color: use the most common dark color in the text region
        (assumes text is darker than background — true for most book text)

    Returns:
        {"font_size": int, "font_color": (B, G, R)}
    """
    x1, y1, x2, y2 = bbox
    h, w = img.shape[:2]

    # Clamp bbox
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)

    region_h = y2 - y1
    region_w = x2 - x1

    # Font size: roughly 70-80% of region height
    if override_size is not None:
        font_size = override_size
    else:
        font_size = max(10, int(region_h * 0.7))

    # Font color
    if override_color is not None:
        font_color = _hex_to_bgr(override_color)
    else:
        # Extract the text region and find the dominant dark color
        region = img[y1:y2, x1:x2]
        if region.size == 0:
            font_color = (0, 0, 0)  # default black
        else:
            # Convert to grayscale, threshold to find dark pixels (likely text)
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            # Text pixels are usually darker — threshold at median
            median_val = np.median(gray)
            dark_mask = gray < median_val

            if np.any(dark_mask):
                # Average color of dark pixels
                dark_pixels = region[dark_mask]
                avg_color = dark_pixels.mean(axis=0).astype(int)
                font_color = tuple(avg_color.tolist())
            else:
                font_color = (0, 0, 0)

    return {
        "font_size": font_size,
        "font_color": font_color,  # BGR
    }


# ── Text Rendering ──────────────────────────────────────────────────────────

def render_text_on_region(
    img: np.ndarray,
    bbox: list[int],
    text: str,
    font_size: int,
    font_color: tuple[int, int, int],
) -> np.ndarray:
    """Render Vietnamese text onto a specific region of the image.

    The text is centered within the bbox, with automatic size reduction
    if it doesn't fit.

    Args:
        img: OpenCV BGR image.
        bbox: [x1, y1, x2, y2] target region.
        text: Vietnamese text to render.
        font_size: Base font size.
        font_color: BGR color tuple.

    Returns:
        Modified image with text rendered.
    """
    x1, y1, x2, y2 = bbox
    region_w = x2 - x1
    region_h = y2 - y1

    # Convert BGR image to PIL RGB for text rendering
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    # Convert font color from BGR to RGB for PIL
    color_rgb = _bgr_to_rgb(font_color)

    # Try progressively smaller font sizes until text fits
    current_size = font_size
    min_size = max(8, font_size // 3)

    while current_size >= min_size:
        font = _get_font(current_size)

        # Measure text bounding box
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        if text_w <= region_w and text_h <= region_h:
            break
        current_size -= 1
    else:
        # Text still doesn't fit at minimum size — render anyway
        font = _get_font(min_size)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

    # Center text in the region
    text_x = x1 + (region_w - text_w) // 2
    text_y = y1 + (region_h - text_h) // 2

    # Draw text
    draw.text(
        (text_x, text_y),
        text,
        font=font,
        fill=color_rgb,
    )

    # Convert back to OpenCV BGR
    result = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return result
