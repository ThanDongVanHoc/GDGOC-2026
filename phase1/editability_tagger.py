"""
Task #p1.3: Editability Tagging — assigns permission levels to content blocks.

Combines global metadata constraints with page layout data to determine
which blocks can be freely edited, partially edited, or must remain locked.
"""

from phase1.models import (
    EditabilityTag,
    GlobalMetadata,
    ImageBlock,
    PageLayout,
    TextBlock,
)


def _check_bbox_overlap(bbox_a: list[float], bbox_b: list[float]) -> bool:
    """Checks whether two bounding boxes overlap.

    Uses axis-aligned bounding box (AABB) intersection test.

    Args:
        bbox_a: First bounding box as [x0, y0, x1, y1].
        bbox_b: Second bounding box as [x0, y0, x1, y1].

    Returns:
        bool: True if the two bounding boxes overlap, False otherwise.
    """
    return not (
        bbox_a[2] <= bbox_b[0]
        or bbox_a[0] >= bbox_b[2]
        or bbox_a[3] <= bbox_b[1]
        or bbox_a[1] >= bbox_b[3]
    )


def _contains_protected_name(content: str, protected_names: list[str]) -> bool:
    """Checks if text content contains any protected character names.

    Performs case-insensitive matching against the list of protected names
    from global metadata.

    Args:
        content: The text content to check.
        protected_names: List of names that must not be translated.

    Returns:
        bool: True if any protected name is found in the content.
    """
    content_lower = content.lower()
    return any(name.lower() in content_lower for name in protected_names)


def _is_copyright_text(content: str) -> bool:
    """Detects whether a text block contains copyright or legal notices.

    Checks for common copyright indicators such as the copyright symbol,
    'all rights reserved', ISBN numbers, etc.

    Args:
        content: The text content to check.

    Returns:
        bool: True if the content appears to be a copyright notice.
    """
    copyright_indicators = [
        "©",
        "copyright",
        "all rights reserved",
        "isbn",
        "published by",
        "printed in",
    ]
    content_lower = content.lower()
    return any(indicator in content_lower for indicator in copyright_indicators)


def tag_text_block(
    text_block: TextBlock,
    metadata: GlobalMetadata,
    image_bboxes: list[list[float]],
) -> TextBlock:
    """Assigns an editability tag to a single text block.

    Logic:
    - NON_EDITABLE if: block is copyright text, or integrity_protection is on
      and block contains protected names, or license is invalid.
    - SEMI_EDITABLE if: block overlaps with an image bounding box (text can
      be translated but underlying image must not be altered).
    - EDITABLE otherwise: full translation rights.

    Args:
        text_block: The text block to tag.
        metadata: Global metadata constraints for the project.
        image_bboxes: List of image bounding boxes on the same page,
            each as [x0, y0, x1, y1].

    Returns:
        TextBlock: The same text block with editability_tag set.
    """
    # Rule 1: License not granted — everything is non-editable
    if not metadata.legal_parameters.license_status:
        text_block.editability_tag = EditabilityTag.NON_EDITABLE
        return text_block

    # Rule 2: Copyright / legal notices are always locked
    if _is_copyright_text(text_block.content):
        text_block.editability_tag = EditabilityTag.NON_EDITABLE
        return text_block

    # Rule 3: Protected names with integrity protection
    protected_names = metadata.ip_brand_parameters.protected_names
    if (
        metadata.legal_parameters.integrity_protection
        and _contains_protected_name(text_block.content, protected_names)
    ):
        text_block.editability_tag = EditabilityTag.SEMI_EDITABLE
        return text_block

    # Rule 4: Text overlapping with images — semi-editable
    for img_bbox in image_bboxes:
        if _check_bbox_overlap(text_block.bbox, img_bbox):
            text_block.editability_tag = EditabilityTag.SEMI_EDITABLE
            return text_block

    # Default: fully editable
    text_block.editability_tag = EditabilityTag.EDITABLE
    return text_block


def tag_image_block(
    image_block: ImageBlock,
    metadata: GlobalMetadata,
) -> ImageBlock:
    """Assigns an editability tag to a single image block.

    Logic:
    - NON_EDITABLE if: no_retouching is true OR license is invalid.
    - EDITABLE if: allow_bg_edit is true and retouching is permitted.
    - SEMI_EDITABLE otherwise.

    Args:
        image_block: The image block to tag.
        metadata: Global metadata constraints for the project.

    Returns:
        ImageBlock: The same image block with editability_tag set.
    """
    if not metadata.legal_parameters.license_status:
        image_block.editability_tag = EditabilityTag.NON_EDITABLE
        return image_block

    if metadata.ip_brand_parameters.no_retouching:
        image_block.editability_tag = EditabilityTag.NON_EDITABLE
        return image_block

    if metadata.editorial_parameters.allow_bg_edit:
        image_block.editability_tag = EditabilityTag.EDITABLE
        return image_block

    image_block.editability_tag = EditabilityTag.SEMI_EDITABLE
    return image_block


def tag_page(page: PageLayout, metadata: GlobalMetadata) -> PageLayout:
    """Applies editability tags to all blocks on a single page.

    Processes every text block and image block on the page, applying
    editability rules based on global metadata constraints and
    spatial overlap analysis.

    Args:
        page: The page layout containing text and image blocks.
        metadata: Global metadata constraints for the project.

    Returns:
        PageLayout: The same page with all blocks tagged.
    """
    image_bboxes = [img.bbox for img in page.image_blocks]

    for i, text_block in enumerate(page.text_blocks):
        page.text_blocks[i] = tag_text_block(text_block, metadata, image_bboxes)

    for i, image_block in enumerate(page.image_blocks):
        page.image_blocks[i] = tag_image_block(image_block, metadata)

    return page


def tag_all_pages(
    pages: list[PageLayout], metadata: GlobalMetadata
) -> list[PageLayout]:
    """Applies editability tags to all blocks across all pages.

    Args:
        pages: List of page layouts from PDF parsing.
        metadata: Global metadata constraints for the project.

    Returns:
        list[PageLayout]: All pages with editability tags applied to every block.
    """
    return [tag_page(page, metadata) for page in pages]
