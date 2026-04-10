"""
Phase 0 — Example Worker: Edge Detection with OpenCV.

=== THIS IS AN EXAMPLE FOR PARTNERS TO STUDY ===

This worker demonstrates the complete pattern:
    1. Receive payload from Orchestrator (via main.py)
    2. Do heavy processing (OpenCV edge detection)
    3. Return results (which main.py sends as webhook)

When building your own Phase, replace the logic in run() with your own code.
"""

import os
import time

import cv2
import numpy as np


async def run(payload: dict) -> dict:
    """
    Main entry point — called by main.py when a job arrives.

    This function does ALL the heavy work. The Orchestrator never sees
    this file — it only communicates through main.py's endpoint + webhook.

    Args:
        payload: Job data from the Orchestrator.
            - image_path (str): Path to input image.
            - (any other fields your Phase needs)

    Returns:
        dict: Results to send back via webhook.
    """
    image_path = payload["image_path"]
    print(f"[Worker] Received job: process image '{image_path}'")

    # ─── Step 1: Load the image ──────────────────────────────────
    image = cv2.imread(image_path)
    if image is None:
        # If no real image, create a sample one for demo purposes
        print("[Worker] Image not found — generating sample image for demo")
        image = _generate_sample_image()
        # Save the sample so we have something to work with
        os.makedirs("data/input", exist_ok=True)
        cv2.imwrite("data/input/sample.png", image)

    height, width = image.shape[:2]
    print(f"[Worker] Image loaded: {width}x{height}")

    # ─── Step 2: Convert to grayscale ────────────────────────────
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print("[Worker] Converted to grayscale")

    # ─── Step 3: Edge detection (Canny) ──────────────────────────
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)
    print("[Worker] Edge detection complete")

    # ─── Step 4: Find contours (like finding text/object regions) ─
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_count = len(contours)
    print(f"[Worker] Found {contour_count} contours")

    # ─── Step 5: Draw contours on original image ─────────────────
    result_image = image.copy()
    cv2.drawContours(result_image, contours, -1, (0, 255, 0), 2)

    # ─── Step 6: Extract bounding boxes (like Phase 1 does for text) ──
    bboxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Filter out tiny noise contours
        if w > 20 and h > 20:
            bboxes.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
            cv2.rectangle(result_image, (x, y), (x + w, y + h), (0, 0, 255), 2)

    print(f"[Worker] Significant regions: {len(bboxes)}")

    # ─── Step 7: Save processed image ────────────────────────────
    os.makedirs("data/output", exist_ok=True)
    output_path = "data/output/processed.png"
    cv2.imwrite(output_path, result_image)
    print(f"[Worker] Saved processed image to '{output_path}'")

    # Simulate some processing time (remove in real code)
    time.sleep(1)

    # ─── Step 8: Return results ──────────────────────────────────
    # This dict is what gets sent back to the Orchestrator via webhook.
    # Design your return data to match what the next Phase needs.
    return {
        "image_width": width,
        "image_height": height,
        "contour_count": contour_count,
        "significant_regions": bboxes,
        "output_path": os.path.abspath(output_path),
    }


def _generate_sample_image() -> np.ndarray:
    """Generate a sample image with shapes for demo purposes."""
    image = np.ones((600, 800, 3), dtype=np.uint8) * 240  # Light gray background

    # Draw some shapes to simulate a book page
    cv2.rectangle(image, (50, 50), (750, 550), (200, 200, 200), -1)  # Page
    cv2.rectangle(image, (100, 80), (700, 160), (180, 180, 180), -1)  # Title area
    cv2.rectangle(image, (100, 200), (400, 500), (150, 150, 150), -1)  # Image area
    cv2.rectangle(image, (430, 200), (700, 300), (170, 170, 170), -1)  # Text block 1
    cv2.rectangle(image, (430, 320), (700, 420), (170, 170, 170), -1)  # Text block 2
    cv2.circle(image, (250, 350), 80, (100, 100, 100), -1)  # Character

    # Add some text
    cv2.putText(image, "Once upon a time...", (110, 130),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 50, 50), 2)
    cv2.putText(image, "The brave hero set", (440, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    cv2.putText(image, "out on a journey.", (440, 280),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)

    return image
