"""Test script for Phase 3 PDF Export with verified_text_pack_vi.json."""

import json
import os
import sys

# Ensure phase3 is in path for imports
sys.path.insert(0, os.path.dirname(__file__))

from util.pdf_exporter import export_localized_pdf


def main():
    # Paths
    base_dir = os.path.dirname(__file__)
    result_path = os.path.join(base_dir, "dummy_data", "verified_text_pack_vi.json")
    # We still use the same source PDF as it's the only one we have
    source_pdf = os.path.join(base_dir, "data", "uploads", "source.pdf")
    output_pdf = os.path.join(base_dir, "output_test", "localized_output_vi.pdf")
    
    # Load dummy result
    print(f"Loading Vietnamese text pack from: {result_path}")
    with open(result_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Manually add source_pdf_path to payload for the exporter
    payload["source_pdf_path"] = source_pdf
    
    # Handle the fact that verified_text_pack_vi.json has pages at root
    # but our exporter expects context_safe_localized_text_pack or similar
    # Actually, export_localized_pdf tries to find text_pack
    # Let's see: payload.get("verified_text_pack", []) or payload.get("pages", [])
    
    print(f"Running export to: {output_pdf}")
    
    # We need to flatten the pages structure if the exporter expects a flat list
    # Let's check pdf_exporter.py: it groups by page_id.
    # So we need a flat list of blocks.
    flat_blocks = []
    for page in payload.get("pages", []):
        page_id = page.get("page_id", 1)
        for block in page.get("text_blocks", []):
            block["page_id"] = page_id
            flat_blocks.append(block)
            
    from util.pdf_exporter import PDFExporter
    exporter = PDFExporter()
    success = exporter.export(source_pdf, flat_blocks, output_pdf)
    
    if success:
        print("SUCCESS: PDF exported successfully with Vietnamese text.")
        print(f"Output file size: {os.path.getsize(output_pdf)} bytes")
    else:
        print("FAILED: PDF export failed.")


if __name__ == "__main__":
    main()
