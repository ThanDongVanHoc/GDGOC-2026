import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.localization_agent import (
    _read_prompt_file,
    _LOCALIZATION_PROMPT_PATH,
    _EXTRACTION_PROMPT_PATH,
    _REWRITE_PROMPT_PATH,
    _VLM_SYSTEM_PROMPT_PATH
)

def test_prompt_loading():
    print("Testing prompt loading...")
    
    prompts = {
        "Localization": _LOCALIZATION_PROMPT_PATH,
        "Extraction": _EXTRACTION_PROMPT_PATH,
        "Rewrite": _REWRITE_PROMPT_PATH,
        "VLM": _VLM_SYSTEM_PROMPT_PATH
    }
    
    for name, path in prompts.items():
        content = _read_prompt_file(path, "FALLBACK")
        if content == "FALLBACK":
            print(f"[FAIL] {name} prompt failed to load from {path}")
            return False
        else:
            print(f"[OK] {name} prompt loaded ({len(content)} chars)")
            
    # Test formatting for Localization prompt
    localization_content = _read_prompt_file(_LOCALIZATION_PROMPT_PATH, "")
    try:
        formatted = localization_content.format(
            protected_names="['Test']",
            never_change_rules="['No change']"
        )
        print("[OK] Localization prompt formatting works")
    except KeyError as e:
        print(f"[FAIL] Localization prompt formatting missing key: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Localization prompt formatting error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    if test_prompt_loading():
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed.")
        sys.exit(1)
