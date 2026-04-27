import sys
import os
from unittest.mock import MagicMock

# 1. Mock dependencies to avoid requiring pydantic or other external packages
# This allows us to test the logic of prompt_builder.py even when the environment
# cannot install the full dependency stack (like the MSYS2 Python 3.14 issue).

# Mock pydantic
mock_pydantic = MagicMock()
sys.modules["pydantic"] = mock_pydantic

# Define a lightweight version of GlobalMetadata that mimics the Pydantic model's behavior
# but uses standard Python classes.
class MockGlobalMetadata:
    def __init__(self, **kwargs):
        # Set defaults
        self.style_register = "general"
        self.target_age_tone = 15
        self.protected_names = []
        self.never_change_rules = []
        self.cultural_localization = True
        
        # Override with provided kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

# Mock core.models
mock_models = MagicMock()
mock_models.GlobalMetadata = MockGlobalMetadata
sys.modules["core.models"] = mock_models

# 2. Import the actual logic we want to test
# We need to add phase3 to the path so app.prompt_builder finds 'app'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app.prompt_builder import build_localization_system_prompt, build_scoring_system_prompt

# 3. Simple Test Suite
def test_style(style_name):
    print(f"Testing style: {style_name}...")
    meta = MockGlobalMetadata(style_register=style_name)
    loc_prompt = build_localization_system_prompt(meta)
    score_prompt = build_scoring_system_prompt(meta)
    
    assert len(loc_prompt) > 0, f"Loc prompt for {style_name} is empty"
    assert len(score_prompt) > 0, f"Score prompt for {style_name} is empty"
    
    # Check if style-specific keywords appear (basic check)
    if style_name == "children_book":
        assert "playful" in loc_prompt.lower()
        assert "Christmas" in score_prompt or "Halloween" in score_prompt
    elif style_name == "manga":
        assert "manga" in loc_prompt.lower()
    
    print(f"  [OK] {style_name}")

def test_constraints():
    print("Testing constraints...")
    meta = MockGlobalMetadata(
        protected_names=["Harry", "Hermione"],
        never_change_rules=["Rule 1: Don't talk about fight club"],
        cultural_localization=False
    )
    
    prompt = build_localization_system_prompt(meta)
    print("Prompt:", prompt)
    assert "Harry" in prompt
    assert "Hermione" in prompt
    assert "Rule 1" in prompt
    assert "DISABLED" in prompt
    print("  [OK] Constraints")

def test_age_calibration():
    print("Testing age calibration...")
    # Test child
    meta_child = MockGlobalMetadata(target_age_tone=6)
    prompt_child = build_localization_system_prompt(meta_child)
    assert "very young" in prompt_child.lower() or "under 8" in prompt_child
    
    # Test adult
    meta_adult = MockGlobalMetadata(target_age_tone=20)
    prompt_adult = build_localization_system_prompt(meta_adult)
    assert "adult" in prompt_adult.lower()
    print("  [OK] Age calibration")

if __name__ == "__main__":
    print("Starting prompt logic verification (No Dependencies Mode)")
    print("==========================================================")
    
    try:
        for style in ["children_book", "manga", "novel", "academic", "general"]:
            test_style(style)
        
        test_constraints()
        test_age_calibration()
        
        print("==========================================================")
        print("SUCCESS: All prompt logic verified correctly!")
    except Exception as e:
        print(f"\nFAILURE: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
