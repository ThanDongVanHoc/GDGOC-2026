"""Entity Graph construction for Phase 3.1 — Global Entity Pre-computation.

Builds and manages the global entity graph data structure that maps
cultural entities, their types, page appearances, and inter-entity
relationships. Supports enrichment via AMR-derived semantic relations.

The entity graph uses an adjacency list representation where each node
stores metadata (type, pages, contexts) and a list of related entity
names (edges). This structure enables millisecond-speed BFS/DFS
traversal for butterfly effect validation.
"""

import logging
from typing import Any, Optional

from core.amr_parser import (
    build_adjacency_from_amr,
    decode_amr_string,
    parse_sentences_to_amr,
)

logger = logging.getLogger(__name__)


def build_entity_graph(text_pack: dict[str, Any], extracted_entities: list[dict[str, Any]]) -> dict[str, dict]:
    """Build the entity graph from a Verified Text Pack and extracted entities.

    Scans all pages and text blocks to identify which entities appear
    in which blocks via substring matching. Co-occurring entities 
    (appearing in the same text block) are automatically linked as related.

    Args:
        text_pack: The Verified Text Pack JSON.
        extracted_entities: List of entity objects parsed via LLM.

    Returns:
        A dictionary representing the entity graph. Keys are entity
        names, values are dicts with 'type', 'pages', 'related',
        and 'contexts' fields.
    """
    entity_graph: dict[str, dict] = {}
    
    # Initialize graph nodes
    for ent in extracted_entities:
        name = ent.get("name", "")
        if not name:
            continue
        entity_graph[name] = {
            "type": ent.get("type", "other"),
            "pages": [],
            "related": [],
            "contexts": [],
        }

    for page in text_pack.get("pages", []):
        page_id = page.get("page_id", 0)

        for block in page.get("text_blocks", []):
            translated = block.get("translated_content", "")
            original = block.get("english_content", "")
            # Search both original block and translated block for entity triggers
            text = f"{translated} {original}" if translated else original
            if not text:
                continue

            # Find matching entities in this block
            block_entities = []
            text_lower = text.lower()
            
            for ent_name in entity_graph.keys():
                if ent_name.lower() in text_lower:
                    block_entities.append(ent_name)
                    
                    node = entity_graph[ent_name]
                    # Track unique page appearances
                    if page_id not in node["pages"]:
                        node["pages"].append(page_id)

                    # Record contextual sentence
                    node["contexts"].append({
                        "page": page_id,
                        "sentence": text,
                    })

            # Build co-occurrence edges within the same text block
            for i, name_a in enumerate(block_entities):
                for name_b in block_entities[i + 1:]:
                    if name_b not in entity_graph[name_a]["related"]:
                        entity_graph[name_a]["related"].append(name_b)
                    if name_a not in entity_graph[name_b]["related"]:
                        entity_graph[name_b]["related"].append(name_a)

    logger.info(
        "Built entity graph with %d entities.", len(entity_graph)
    )
    return entity_graph


def merge_amr_into_entity_graph(
    entity_graph: dict[str, dict],
    sentences: list[str],
    amr_graphs: Optional[list[str]] = None,
) -> dict[str, list[dict[str, str]]]:
    """Enrich the entity graph with AMR-derived semantic relations.

    Parses sentences into AMR graphs (or uses pre-parsed ones),
    then extracts semantic edges to produce a combined AMR adjacency
    dict. This provides richer relation types (e.g., :ARG0, :location)
    beyond simple co-occurrence.

    Args:
        entity_graph: The base entity graph from build_entity_graph().
        sentences: The source English sentences to parse with AMR.
        amr_graphs: Optional pre-parsed AMR graph strings. If None,
            sentences will be parsed using the loaded AMR model.

    Returns:
        A combined AMR adjacency dict merging all sentence-level AMR
        graphs. Keys are concept names, values are lists of
        {concept, relation} neighbor dicts.
    """
    if amr_graphs is None:
        amr_graphs = parse_sentences_to_amr(sentences)

    combined_adjacency: dict[str, list[dict[str, str]]] = {}

    for amr_string in amr_graphs:
        if amr_string is None:
            continue

        try:
            graph = decode_amr_string(amr_string)
            adjacency = build_adjacency_from_amr(graph)

            # Merge sentence-level adjacency into the combined dict
            for concept, neighbors in adjacency.items():
                if concept not in combined_adjacency:
                    combined_adjacency[concept] = []

                for neighbor in neighbors:
                    # Deduplicate by (concept, relation) pair
                    existing_pairs = {
                        (n["concept"], n["relation"])
                        for n in combined_adjacency[concept]
                    }
                    key = (neighbor["concept"], neighbor["relation"])
                    if key not in existing_pairs:
                        combined_adjacency[concept].append(neighbor)

        except Exception as e:
            logger.warning("Failed to decode AMR graph: %s", e)
            continue

    logger.info(
        "Merged AMR adjacency with %d concept nodes.",
        len(combined_adjacency),
    )
    return combined_adjacency


def get_entity_subgraph(
    entity_graph: dict[str, dict],
    entity_name: str,
    max_depth: int = 3,
) -> dict[str, dict]:
    """Extract a subgraph centered on a specific entity.

    Performs BFS from the given entity to collect all reachable
    entities within max_depth hops. Useful for isolating the
    impact zone of a localization proposal.

    Args:
        entity_graph: The full entity graph.
        entity_name: The center entity to start from.
        max_depth: Maximum BFS depth (default: 3).

    Returns:
        A subset of the entity graph containing only entities
        reachable within max_depth hops from entity_name.
    """
    if entity_name not in entity_graph:
        return {}

    subgraph: dict[str, dict] = {}
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(entity_name, 0)]

    while queue:
        current, depth = queue.pop(0)
        if current in visited or depth > max_depth:
            continue
        visited.add(current)

        if current in entity_graph:
            subgraph[current] = entity_graph[current]
            for related in entity_graph[current].get("related", []):
                if related not in visited:
                    queue.append((related, depth + 1))

    return subgraph
