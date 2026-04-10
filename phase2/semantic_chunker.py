"""
Task #p2.1: Semantic Chunking — groups text blocks for batch translation.

Splits text blocks from the Phase 1 Standardized Pack into manageable
chunks of approximately 10-15 pages per API call to avoid context window
overflow and reduce LLM hallucination risk.
"""

from phase2.models import SemanticChunk, SourceTextBlock

PAGES_PER_CHUNK = 10


def create_chunks_from_standardized_pack(
    standardized_pack: dict,
) -> list[SemanticChunk]:
    """Creates semantic chunks from a Phase 1 Standardized Pack.

    Groups text blocks by pages, with each chunk containing approximately
    PAGES_PER_CHUNK pages. Preserves the original bbox mapping for each
    text block so Phase 4 can reconstruct the layout.

    Args:
        standardized_pack: Full Standardized Pack dictionary from Phase 1
            containing 'pages' with text_blocks and image_blocks.

    Returns:
        list[SemanticChunk]: A list of semantic chunks, each containing
            a subset of pages' text blocks ready for translation.
    """
    pages = standardized_pack.get("pages", [])
    chunks: list[SemanticChunk] = []
    chunk_id = 1

    for i in range(0, len(pages), PAGES_PER_CHUNK):
        page_batch = pages[i : i + PAGES_PER_CHUNK]
        page_ids: list[int] = []
        text_blocks: list[SourceTextBlock] = []

        for page in page_batch:
            page_id = page.get("page_id", 0)
            page_ids.append(page_id)

            for block in page.get("text_blocks", []):
                text_blocks.append(
                    SourceTextBlock(
                        content=block.get("content", ""),
                        bbox=block.get("bbox", [0, 0, 0, 0]),
                        font=block.get("font", ""),
                        size=block.get("size", 0.0),
                        color=block.get("color", 0),
                        flags=block.get("flags", 0),
                        editability_tag=block.get("editability_tag", "editable"),
                    )
                )

        if text_blocks:
            chunks.append(
                SemanticChunk(
                    chunk_id=chunk_id,
                    page_range=page_ids,
                    text_blocks=text_blocks,
                )
            )
            chunk_id += 1

    return chunks
