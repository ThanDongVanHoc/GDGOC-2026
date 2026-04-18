import os
import sys
from pathlib import Path

# Add core to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

from localization_agent import _resolve_pdf_path

def test_resolution():
    # 1. Test absolute path
    abs_path = os.path.abspath("phase3/data/uploads/source.pdf")
    # Replace backslashes with forward slashes to simulate user input
    user_abs = abs_path.replace("\\", "/")
    
    resolved = _resolve_pdf_path(user_abs)
    print(f"Input Absolute: {user_abs}")
    print(f"Resolved:       {resolved}")
    assert os.path.isabs(resolved), "Should return absolute path"
    assert os.path.exists(resolved), "Resolved path should exist"
    
    # 2. Test relative path (project root relative)
    rel_path = "phase3/data/uploads/source.pdf"
    resolved_rel = _resolve_pdf_path(rel_path)
    print(f"\nInput Relative: {rel_path}")
    print(f"Resolved:       {resolved_rel}")
    assert os.path.exists(resolved_rel)
    
    # 3. Test fallback (just the filename)
    filename = "source.pdf"
    resolved_fb = _resolve_pdf_path(filename)
    print(f"\nInput Filename: {filename}")
    print(f"Resolved:       {resolved_fb}")
    assert os.path.exists(resolved_fb), "Should find it via fallback"
    assert "data/uploads/source.pdf" in resolved_fb.replace("\\", "/")

    print("\nSUCCESS: Path resolution logic verified!")

if __name__ == "__main__":
    test_resolution()
