import json
import os
import sys
from pydantic import ValidationError

# Add the current directory to sys.path to import core.models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.models import Phase3InputPayload

def test_payload_compatibility():
    payload_path = os.path.join(os.path.dirname(__file__), "dummy_data", "phase3_payload.json")
    
    if not os.path.exists(payload_path):
        print(f"Error: {payload_path} not found.")
        return

    with open(payload_path, "r", encoding="utf-8") as f:
        payload_data = json.load(f)

    print("Attempting to validate phase3_payload.json...")
    try:
        # Pydantic validation
        validated = Phase3InputPayload(**payload_data)
        print("Success! Payload is compatible with the updated Phase3InputPayload model.")
        
        # Check specific fields
        print(f"Thread ID: {validated.thread_id}")
        print(f"Webhook URL (optional): {validated.webhook_url}")
        print(f"Target Language: {validated.global_metadata.target_language}")
        print(f"Cultural Localization: {validated.global_metadata.cultural_localization}")
        
    except ValidationError as e:
        print("Validation Failed!")
        print(e.json(indent=2))
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_payload_compatibility()
