"""Test script for Phase 3 PDF Export functionality."""

import json
import os
import sys

# Ensure phase3 is in path for imports
sys.path.insert(0, os.path.dirname(__file__))

from util.pdf_exporter import export_localized_pdf


def main():
    # Paths
    base_dir = os.path.dirname(__file__)
    result_path = os.path.join(base_dir, "dummy_data", "phase3_result.json")
    output_pdf = os.path.join(base_dir, "output_test", "localized_output.pdf")
    
    # Load dummy result
    print(f"Loading Phase 3 result from: {result_path}")
    with open(result_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    
    # Override source_pdf_path if it doesn't exist to use the local one
    # This handles cases where the path in dummy data was for another machine
    source_pdf = payload.get("output_phase_3", {}).get("source_pdf_path")
    local_source = os.path.join(base_dir, "data", "uploads", "source.pdf")
    
    if not source_pdf or not os.path.exists(source_pdf):
        print(f"Overriding source_pdf_path to local: {local_source}")
        payload["output_phase_3"]["source_pdf_path"] = local_source
    
    print(f"Running export to: {output_pdf}")
    success = export_localized_pdf(payload, output_pdf)
    
    if success:
        print("SUCCESS: PDF exported successfully.")
        print(f"Output file size: {os.path.getsize(output_pdf)} bytes")
    else:
        print("FAILED: PDF export failed.")


if __name__ == "__main__":
    main()
