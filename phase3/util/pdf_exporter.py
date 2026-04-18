"""PDF Exporter Utility for Phase 3 — Cultural Localization.

Provides functionality to overlay localized Vietnamese text onto the original
source PDF using bounding box coordinates from the localization pack.
"""

import logging
import os
from typing import Any, Optional

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFExporter:
    """Utility to generate localized PDFs by overlaying text on original source PDFs."""

    def __init__(self, fallback_font_path: Optional[str] = None):
        """
        Initialize the PDF exporter.

        Args:
            fallback_font_path: Optional path to a .ttf font file supporting Vietnamese.
                If not provided, it will attempt to find a system font.
        """
        # Common Windows system font paths that support Vietnamese
        self.font_search_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", # Linux fallback
        ]
        self.font_path = fallback_font_path
        
        if not self.font_path:
            for path in self.font_search_paths:
                if os.path.exists(path):
                    self.font_path = path
                    break
        
        if not self.font_path:
            logger.warning("[PDFExporter] No Vietnamese-compatible font found. Text might render incorrectly.")

    def export(
        self, 
        source_pdf_path: str, 
        localized_text_pack: list[dict[str, Any]], 
        output_pdf_path: str
    ) -> bool:
        """
        Overlay localized text onto the source PDF and save the result.

        Args:
            source_pdf_path: Path to the original input PDF.
            localized_text_pack: List of dictionaries containing localized_content, bbox, and page_id.
            output_pdf_path: Path where the resulting PDF should be saved.

        Returns:
            bool: True if export was successful, False otherwise.
        """
        if not os.path.exists(source_pdf_path):
            logger.error(f"[PDFExporter] Source PDF not found: {source_pdf_path}")
            return False

        try:
            doc = fitz.open(source_pdf_path)
            
            # Group text blocks by page_id for efficiency
            pages_map: dict[int, list[dict]] = {}
            for block in localized_text_pack:
                page_id = block.get("page_id", 1)
                if page_id not in pages_map:
                    pages_map[page_id] = []
                pages_map[page_id].append(block)

            for page_id, blocks in pages_map.items():
                # page_id is usually 1-indexed in our system
                page_idx = page_id - 1
                if page_idx < 0 or page_idx >= len(doc):
                    logger.warning(f"[PDFExporter] Page ID {page_id} out of range for PDF.")
                    continue
                
                page = doc[page_idx]
                
                for block in blocks:
                    self._process_text_block(page, block)

            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
            
            doc.save(output_pdf_path)
            doc.close()
            logger.info(f"[PDFExporter] Successfully exported localized PDF to: {output_pdf_path}")
            return True

        except Exception as e:
            logger.error(f"[PDFExporter] PDF export failed: {e}")
            return False

    def _process_text_block(self, page: fitz.Page, block: dict[str, Any]) -> None:
        """
        Clear the original area and write the localized text onto the page.

        Args:
            page: The PyMuPDF page object.
            block: The dictionary containing text block data.
        """
        # Get localized content (prefer localized_content if present, else translated_content)
        text = block.get("localized_content") or block.get("translated_content") or block.get("text")
        if not text:
            return

        bbox = block.get("bbox")
        if not bbox or len(bbox) != 4:
            return

        # bbox is [x0, y0, x1, y1]
        rect = fitz.Rect(bbox)
        
        # 1. Clear original area with a white rectangle to prevent overprinting
        # Only do this for 'text' type blocks usually, not OCR if the OCR bbox is the whole panel.
        # However, for simplicity and safer overlay, we clear it.
        # Note: If background editing is disabled, we might want to skip this.
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

        # 2. Insert new text
        # Use font size and color from block if available, else defaults
        font_size = block.get("size", 12.0)
        # color in our pack is usually a decimal number (like 2899536)
        color_dec = block.get("color", 0)
        
        # Convert decimal color to RGB (0-1 range)
        # Assuming our color is (R << 16) | (G << 8) | B
        r = ((color_dec >> 16) & 255) / 255.0
        g = ((color_dec >> 8) & 255) / 255.0
        b = (color_dec & 255) / 255.0
        
        # Add text
        try:
            # We use insert_textbox for better wrapping if the text is long
            # However, insert_text is simpler if coordinates are precise
            page.insert_textbox(
                rect,
                text,
                fontsize=font_size,
                fontname="helv",  # Standard font fallback
                fontfile=self.font_path,
                color=(r, g, b),
                align=fitz.TEXT_ALIGN_LEFT
            )
        except Exception as e:
            logger.error(f"[PDFExporter] Failed to insert text at {bbox}: {e}")

# Factory function for backward compatibility or easy access
def export_localized_pdf(payload: dict, output_path: str) -> bool:
    """
    High-level function to export a PDF from a Phase 3 result payload.
    
    Args:
        payload: The complete Phase 3 result dictionary.
        output_path: Target path for the PDF.
    """
    exporter = PDFExporter()
    
    # Try to extract data based on API contract
    source_pdf = payload.get("source_pdf_path")
    
    # Check if nested in output_phase_3 (result format)
    if "output_phase_3" in payload:
        res = payload["output_phase_3"]
        source_pdf = source_pdf or res.get("source_pdf_path")
        text_pack = res.get("context_safe_localized_text_pack", [])
    else:
        # Check if it's the input payload format
        if "output_phase_2" in payload:
            text_pack = payload["output_phase_2"].get("verified_text_pack", [])
        else:
            text_pack = payload.get("verified_text_pack", [])

    if not source_pdf:
        # Final fallback check in root or try to resolve from absolute to relative
        source_pdf = payload.get("source_pdf_path", "")

    return exporter.export(source_pdf, text_pack, output_path)
