"""
OCR service – EasyOCR reader management and image annotation helpers.
"""

import cv2
import numpy as np
import easyocr


# Initialize EasyOCR reader once (lazy-loaded on first request)
_reader: easyocr.Reader | None = None


def get_reader() -> easyocr.Reader:
    """Lazy-load EasyOCR reader to avoid slow startup."""
    global _reader
    if _reader is None:
        # Support English and Vietnamese; add more languages as needed
        _reader = easyocr.Reader(["en", "vi"], gpu=True)
    return _reader


def draw_bounding_boxes(
    image: np.ndarray,
    results: list,
) -> np.ndarray:
    """Draw bounding boxes and text labels on the image.

    Args:
        image: BGR numpy array from OpenCV.
        results: EasyOCR detection results list of (bbox, text, confidence).

    Returns:
        Annotated BGR numpy array.
    """
    annotated = image.copy()

    for bbox, text, confidence in results:
        # bbox is a list of 4 points: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        pts = np.array(bbox, dtype=np.int32).reshape((-1, 1, 2))

        # Draw the polygon bounding box
        cv2.polylines(annotated, [pts], isClosed=True, color=(0, 255, 0), thickness=2)

        # Put label text above the top-left corner
        top_left = (int(bbox[0][0]), int(bbox[0][1]))
        label = f"{text} ({confidence:.2f})"
        cv2.putText(
            annotated,
            label,
            (top_left[0], top_left[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )

    return annotated
