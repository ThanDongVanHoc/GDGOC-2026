import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.worker import _filter_locked_keywords, _check_bbox_overflow
from core.models import LocalizationProposal

def test_filters():
    proposals = [
        # Should be rejected (protected name)
        LocalizationProposal(
            proposal_id="1",
            original="Harry",
            proposed="Hải",
            affected_pages=[1],
            rationale="localize name"
        ),
        # Should be rejected (never_change_rule)
        LocalizationProposal(
            proposal_id="2",
            original="Snowman",
            proposed="Mudman",
            affected_pages=[1],
            rationale="localize to mud"
        ),
        # Should be rejected (color lock)
        LocalizationProposal(
            proposal_id="3",
            original="red",
            proposed="xanh",
            affected_pages=[1],
            rationale="change color"
        ),
        # Should be allowed
        LocalizationProposal(
            proposal_id="4",
            original="Fireplace",
            proposed="Bếp củi",
            affected_pages=[1],
            rationale="localize objects"
        )
    ]
    
    global_metadata = {
        "protected_names": ["Harry", "Ron"],
        "never_change_rules": ["do not change Snowman to Mudman ever!"],
        "preserve_main_names": True,
        "lock_character_color": True
    }
    
    allowed, rejected = _filter_locked_keywords(proposals, global_metadata)
    print("Allowed:")
    for p in allowed:
        print(" -", p.original, "->", p.proposed)
    print("Rejected:")
    for r in rejected:
        print(" -", r["original"], "->", r["proposed"], "| Reason:", r["conflicts"][0]["reason"])

def test_bbox():
    orig_pack = {
        "pages": [{
            "page_id": 1,
            "text_blocks": [
                {
                    "content": "Short",
                    "bbox": [0, 0, 50, 15], # small box => width 50, height 15
                    "size": 12.0
                },
                {
                    "content": "Normal",
                    "bbox": [0, 0, 100, 20],
                    "size": 12.0
                }
            ]
        }]
    }
    loc_pack = {
        "pages": [{
            "page_id": 1,
            "text_blocks": [
                {
                    "content": "This is a very very long string that will definitely overflow the box",
                    "bbox": [0, 0, 50, 15],
                    "size": 12.0
                },
                {
                    "content": "Normal",
                    "bbox": [0, 0, 100, 20],
                    "size": 12.0
                }
            ]
        }]
    }
    
    warnings = _check_bbox_overflow(orig_pack, loc_pack)
    print("Overflow Warnings:")
    for w in warnings:
        print(" - Page", w["page_id"], "Block", w["block_index"], ":", w["original_content"], "->", w["localized_content"])
        print("   Estimated Max Chars:", w["max_estimated_chars"], "| Actual chars:", w["actual_chars"], "| Ratio:", w["overflow_ratio"])

if __name__ == "__main__":
    print("--- Testing Locked Keywords Filter ---")
    test_filters()
    print("\n--- Testing BBox Overflow Check ---")
    test_bbox()
