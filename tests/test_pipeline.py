"""
End-to-end test for Phase 1 (Ingestion & Structural Parsing)
and Phase 2 (Constrained Translation & Feedback Loop).

Runs against the test.pdf file in the project root to verify
the complete pipeline from PDF parsing to verified translation.
"""

import json
import logging
import os
import sys

# Add parent directory to sys.path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phase1.editability_tagger import tag_all_pages
from phase1.models import GlobalMetadata, StandardizedPack
from phase1.pdf_parser import parse_pdf
from phase2.feedback_loop import process_all_chunks
from phase2.semantic_chunker import create_chunks_from_standardized_pack

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_PDF_PATH = os.path.join(PROJECT_ROOT, "..", "test.pdf")
METADATA_PATH = os.path.join(PROJECT_ROOT, "phase1", "global_metadata.json")

# Gemini API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def test_phase1_pdf_parsing() -> dict:
    """Tests Phase 1 Task #p1.2: PDF structural parsing.

    Parses test.pdf and validates that text blocks and image blocks
    are correctly extracted with bounding box coordinates.

    Returns:
        dict: The standardized pack as a dictionary for Phase 2 testing.

    Raises:
        AssertionError: If parsing produces unexpected results.
    """
    print("\n" + "=" * 70)
    print("PHASE 1 TEST — Task #p1.2: PDF Structural Parsing")
    print("=" * 70)

    # Parse PDF and limit to 10 pages for faster testing
    pages = parse_pdf(TEST_PDF_PATH)
    pages = pages[:10]
    assert len(pages) > 0, "No pages extracted from test.pdf"
    print(f"[PASS] Extracted {len(pages)} page(s) from test.pdf (limited to 10)")

    # Validate page structure
    for page in pages:
        assert page.page_id > 0, f"Invalid page_id: {page.page_id}"
        assert page.width > 0, f"Invalid width: {page.width}"
        assert page.height > 0, f"Invalid height: {page.height}"
        print(
            f"  Page {page.page_id}: {page.width:.1f} x {page.height:.1f} pts, "
            f"{len(page.text_blocks)} text blocks, "
            f"{len(page.image_blocks)} image blocks"
        )

    # Validate text blocks have content and bbox
    total_text_blocks = sum(len(p.text_blocks) for p in pages)
    total_image_blocks = sum(len(p.image_blocks) for p in pages)
    print(f"[PASS] Total: {total_text_blocks} text blocks, {total_image_blocks} image blocks")

    # Validate bbox coordinates
    for page in pages:
        for block in page.text_blocks:
            assert len(block.bbox) == 4, f"Invalid bbox length: {block.bbox}"
            assert block.content, "Empty text block content"
            assert block.bbox[0] <= block.bbox[2], f"Invalid x coords: {block.bbox}"
            assert block.bbox[1] <= block.bbox[3], f"Invalid y coords: {block.bbox}"
    print("[PASS] All bounding box coordinates are valid")

    # Show sample text blocks
    if pages and pages[0].text_blocks:
        print("\n  Sample text blocks from page 1:")
        for block in pages[0].text_blocks[:5]:
            print(f"    - \"{block.content[:60]}...\" " if len(block.content) > 60 else f"    - \"{block.content}\" ")
            print(f"      bbox={block.bbox}, font={block.font}, size={block.size}")

    return pages


def test_phase1_editability_tagging(pages: list) -> list:
    """Tests Phase 1 Task #p1.3: Editability tagging.

    Applies editability tags based on global_metadata constraints
    and validates the tagging logic.

    Args:
        pages: List of PageLayout objects from PDF parsing.

    Returns:
        list: Tagged pages for standardized pack assembly.

    Raises:
        AssertionError: If tagging produces unexpected results.
    """
    print("\n" + "=" * 70)
    print("PHASE 1 TEST — Task #p1.3: Editability Tagging")
    print("=" * 70)

    # Load global metadata
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata_dict = json.load(f)
    metadata = GlobalMetadata(**metadata_dict)
    print(f"[PASS] Loaded global_metadata.json")
    print(f"  Protected names: {metadata.ip_brand_parameters.protected_names}")
    print(f"  No retouching: {metadata.ip_brand_parameters.no_retouching}")

    # Apply tags
    tagged_pages = tag_all_pages(pages, metadata)
    print(f"[PASS] Applied editability tags to {len(tagged_pages)} page(s)")

    # Count tags
    tag_counts = {"editable": 0, "semi-editable": 0, "non-editable": 0}
    for page in tagged_pages:
        for block in page.text_blocks:
            tag_counts[block.editability_tag.value] += 1
        for block in page.image_blocks:
            tag_counts[block.editability_tag.value] += 1

    for tag, count in tag_counts.items():
        print(f"  {tag}: {count} blocks")

    # Validate that image blocks with no_retouching=true are non-editable
    if metadata.ip_brand_parameters.no_retouching:
        for page in tagged_pages:
            for img in page.image_blocks:
                assert img.editability_tag.value == "non-editable", (
                    f"Image block should be non-editable when no_retouching=true"
                )
        print("[PASS] All image blocks correctly tagged as non-editable (no_retouching=true)")

    return tagged_pages


def test_phase1_standardized_pack(tagged_pages: list) -> dict:
    """Tests Phase 1 Task #p1.4: Standardized Pack assembly.

    Builds the full Standardized Pack and validates its structure.

    Args:
        tagged_pages: List of tagged PageLayout objects.

    Returns:
        dict: The standardized pack as a dictionary.

    Raises:
        AssertionError: If the pack structure is invalid.
    """
    print("\n" + "=" * 70)
    print("PHASE 1 TEST — Task #p1.4: Standardized Pack")
    print("=" * 70)

    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        metadata_dict = json.load(f)
    metadata = GlobalMetadata(**metadata_dict)

    pack = StandardizedPack(
        global_metadata=metadata,
        pages=tagged_pages,
    )

    pack_dict = pack.model_dump()
    assert "global_metadata" in pack_dict, "Missing global_metadata"
    assert "pages" in pack_dict, "Missing pages"
    assert len(pack_dict["pages"]) > 0, "No pages in pack"
    print(f"[PASS] Standardized Pack assembled with {len(pack_dict['pages'])} page(s)")

    # Validate JSON serialization
    pack_json = json.dumps(pack_dict, ensure_ascii=False, indent=2)
    assert len(pack_json) > 0, "Serialization produced empty output"
    print(f"[PASS] JSON serialization successful ({len(pack_json)} characters)")

    # Save output for inspection
    output_path = os.path.join(PROJECT_ROOT, "tests", "phase1_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pack_json)
    print(f"[INFO] Output saved to {output_path}")

    return pack_dict


def test_phase2_semantic_chunking(standardized_pack: dict) -> list:
    """Tests Phase 2 Task #p2.1: Semantic chunking.

    Creates semantic chunks from the Standardized Pack and validates
    that bbox coordinates are preserved.

    Args:
        standardized_pack: The full Standardized Pack dictionary.

    Returns:
        list: List of SemanticChunk objects.

    Raises:
        AssertionError: If chunking produces unexpected results.
    """
    print("\n" + "=" * 70)
    print("PHASE 2 TEST — Task #p2.1: Semantic Chunking")
    print("=" * 70)

    chunks = create_chunks_from_standardized_pack(standardized_pack)
    assert len(chunks) > 0, "No chunks created"
    print(f"[PASS] Created {len(chunks)} semantic chunk(s)")

    for chunk in chunks:
        print(
            f"  Chunk {chunk.chunk_id}: "
            f"pages {chunk.page_range}, "
            f"{len(chunk.text_blocks)} text blocks"
        )
        # Validate bbox preservation
        for block in chunk.text_blocks:
            assert len(block.bbox) == 4, f"Bbox lost during chunking: {block.bbox}"
        print(f"  [PASS] All bounding boxes preserved in chunk {chunk.chunk_id}")

    return chunks


def test_phase2_translation_pipeline(chunks: list, standardized_pack: dict) -> None:
    """Tests Phase 2 Tasks #p2.2-p2.4: Translation + Feedback Loop.

    Runs the full Translator ↔ Reviser feedback loop on each chunk
    using the Gemini API.

    Args:
        chunks: List of SemanticChunk objects to translate.
        standardized_pack: The full Standardized Pack for global metadata.

    Raises:
        AssertionError: If translation pipeline produces unexpected results.
    """
    print("\n" + "=" * 70)
    print("PHASE 2 TEST — Tasks #p2.2-p2.4: Translation + Feedback Loop")
    print("=" * 70)

    if not GEMINI_API_KEY:
        print("[SKIP] GEMINI_API_KEY not set — skipping translation tests")
        return

    global_metadata = standardized_pack.get("global_metadata", {})

    results = process_all_chunks(
        chunks=chunks,
        global_metadata=global_metadata,
        api_key=GEMINI_API_KEY,
    )

    assert len(results) == len(chunks), (
        f"Expected {len(chunks)} results, got {len(results)}"
    )
    print(f"[PASS] Processed {len(results)} chunk(s)")

    total_blocks = 0
    warning_blocks = 0

    for pack in results:
        print(f"\n  Chunk {pack.chunk_id}:")
        print(f"    Translated blocks: {len(pack.translated_blocks)}")
        print(f"    Warnings: {len(pack.warnings)} block(s)")

        for block in pack.translated_blocks:
            assert block.bbox, "Bbox lost during translation"
            assert block.translated_content, "Empty translation"
            total_blocks += 1

            if block.warning.value == "warning":
                warning_blocks += 1

        # Show sample translations
        if pack.translated_blocks:
            sample = pack.translated_blocks[0]
            print(f"    Sample:")
            print(f"      Original: \"{sample.original_content[:80]}\"")
            print(f"      Translated: \"{sample.translated_content[:80]}\"")
            print(f"      Score: {sample.score}")

    print(f"\n[PASS] Total: {total_blocks} blocks translated, {warning_blocks} warnings")

    # Save Phase 2 output
    output_path = os.path.join(PROJECT_ROOT, "tests", "phase2_output.json")
    results_dict = [r.model_dump() for r in results]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_dict, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Output saved to {output_path}")


def main() -> None:
    """Runs the complete end-to-end test pipeline.

    Executes all Phase 1 and Phase 2 tests sequentially,
    using test.pdf as the input file.
    """
    print("=" * 70)
    print("OmniLocal E2E Pipeline Test")
    print(f"Test PDF: {TEST_PDF_PATH}")
    print(f"Metadata: {METADATA_PATH}")
    print(f"Gemini API Key: {'SET' if GEMINI_API_KEY else 'NOT SET'}")
    print("=" * 70)

    # Phase 1 Tests
    pages = test_phase1_pdf_parsing()
    tagged_pages = test_phase1_editability_tagging(pages)
    standardized_pack = test_phase1_standardized_pack(tagged_pages)

    # Phase 2 Tests
    chunks = test_phase2_semantic_chunking(standardized_pack)
    test_phase2_translation_pipeline(chunks, standardized_pack)

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
