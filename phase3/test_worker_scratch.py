import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.worker import (
    _filter_locked_keywords,
    _check_bbox_overflow,
    _serialize_localized_text_pack,
)
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
                    "bbox": [0, 0, 50, 15],  # small box => width 50, height 15
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


def test_serialize():
    """Test _serialize_localized_text_pack produces API-contract-compliant output.

    Verifies:
      - Safe blocks land in context_safe_localized_text_pack
      - Overflow blocks are excluded from safe pack and appear in warnings
      - All required fields are present per API_CONTRACT.md Phase 3 schema
    """
    orig_pack = {
        "pages": [{
            "page_id": 1,
            "text_blocks": [
                {
                    "content": "Hello world",
                    "bbox": [0, 0, 200, 30],
                    "size": 12.0,
                    "font": "Arial",
                    "color": 0,
                    "flags": 0,
                },
                {
                    "content": "Short",
                    "bbox": [0, 0, 40, 15],
                    "size": 12.0,
                    "font": "Arial",
                    "color": 0,
                    "flags": 0,
                },
            ]
        }]
    }

    loc_pack = {
        "pages": [{
            "page_id": 1,
            "text_blocks": [
                {
                    "content": "Xin chào thế giới",
                    "bbox": [0, 0, 200, 30],
                    "size": 12.0,
                    "font": "Arial",
                    "color": 0,
                    "flags": 0,
                },
                {
                    "content": "This text is way too long for the tiny bounding box allocated",
                    "bbox": [0, 0, 40, 15],
                    "size": 12.0,
                    "font": "Arial",
                    "color": 0,
                    "flags": 0,
                },
            ]
        }]
    }

    overflow_warnings = [
        {
            "page_id": 1,
            "block_index": 1,
            "original_content": "Short",
            "localized_content": "This text is way too long for the tiny bounding box allocated",
            "max_estimated_chars": 6,
            "actual_chars": 60,
            "overflow_ratio": 10.0,
        }
    ]

    safe_pack, warnings = _serialize_localized_text_pack(
        localized_pack=loc_pack,
        original_pack=orig_pack,
        overflow_warnings=overflow_warnings,
    )

    print("\n--- context_safe_localized_text_pack ---")
    assert len(safe_pack) == 1, f"Expected 1 safe block, got {len(safe_pack)}"
    for entry in safe_pack:
        print(f"  original: {entry['original_content']}")
        print(f"  localized: {entry['localized_content']}")
        print(f"  page_id: {entry['page_id']}, source_type: {entry['source_type']}")
        print(f"  font: {entry['font']}, size: {entry['size']}, color: {entry['color']}, flags: {entry['flags']}")
        print(f"  bbox: {entry['bbox']}, warning: {entry['warning']}")

        # Validate all required keys exist per API contract
        required_keys = {
            "original_content", "localized_content", "bbox", "page_id",
            "source_type", "font", "size", "color", "flags", "warning",
        }
        missing = required_keys - set(entry.keys())
        assert not missing, f"Missing keys in safe pack entry: {missing}"

    print("\n--- localization_warnings ---")
    assert len(warnings) == 1, f"Expected 1 warning, got {len(warnings)}"
    for w in warnings:
        print(f"  page_id: {w['page_id']}, block_index: {w['block_index']}")
        print(f"  original: {w['original_content']} -> localized: {w['localized_content']}")
        print(f"  max_chars: {w['max_estimated_chars']}, actual: {w['actual_chars']}, ratio: {w['overflow_ratio']}")

    print("\n✅ Serialization test PASSED — output matches API contract schema.")


if __name__ == "__main__":
    print("--- Testing Locked Keywords Filter ---")
    test_filters()
    print("\n--- Testing BBox Overflow Check ---")
    test_bbox()
    print("\n--- Testing Serialization (API Contract Compliance) ---")
    test_serialize()
