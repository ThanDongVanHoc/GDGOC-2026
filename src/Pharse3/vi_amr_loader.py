"""Vietnamese AMR dataset loader using ViAMR-v1.0 from HuggingFace.

Loads and indexes the ViAMR-v1.0 dataset (MochiVN/ViAMR-v1.0) which
contains Vietnamese sentences annotated with AMR graphs in PENMAN format.
Builds concept frequency indices and relation mappings to support
cross-lingual energy computation for butterfly effect analysis.

Dataset sources:
    - VLSP 2025 Semantic Parsing: ~2,500 manually annotated Vietnamese sentences
    - Translated AMR 3.0: ~9,000 examples from English AMR 3.0
    - Total: ~185,000 rows

Reference:
    https://huggingface.co/datasets/MochiVN/ViAMR-v1.0
"""

import logging
import re
from collections import Counter, defaultdict
from typing import Any, Optional

import penman
from penman import Graph as PenmanGraph

logger = logging.getLogger(__name__)

# Module-level cache for the loaded dataset index
_vi_amr_index: Optional[dict[str, Any]] = None
_vi_amr_raw_entries: list[dict[str, str]] = []


def load_viamr_dataset(
    max_samples: Optional[int] = None,
    cache_dir: Optional[str] = None,
) -> dict[str, Any]:
    """Load the ViAMR-v1.0 dataset from HuggingFace and build indices.

    Downloads the dataset on first call and caches it locally.
    Builds frequency indices for concepts, relations, and
    concept-relation patterns observed in Vietnamese AMR graphs.

    Args:
        max_samples: Optional limit on the number of samples to load.
            Useful for testing or memory-constrained environments.
            If None, loads the entire dataset.
        cache_dir: Optional directory for caching the downloaded dataset.
            If None, uses the HuggingFace default cache location.

    Returns:
        A dictionary containing the indexed data with keys:
            - 'concept_freq': Counter of concept occurrences
            - 'relation_freq': Counter of relation occurrences
            - 'concept_pairs': Counter of (concept, relation, concept) triples
            - 'concept_to_relations': Mapping from concept to its common relations
            - 'total_graphs': Number of successfully parsed graphs
            - 'total_sentences': Number of sentences in the dataset

    Raises:
        ImportError: If the datasets library is not installed.
        ConnectionError: If the dataset cannot be downloaded.
    """
    global _vi_amr_index, _vi_amr_raw_entries

    if _vi_amr_index is not None:
        return _vi_amr_index

    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError(
            "The 'datasets' library is required. "
            "Install with: pip install datasets"
        ) from e

    logger.info("Loading ViAMR-v1.0 dataset from HuggingFace...")

    try:
        dataset = load_dataset(
            "MochiVN/ViAMR-v1.0",
            cache_dir=cache_dir,
        )
    except Exception as e:
        logger.error("Failed to download ViAMR-v1.0: %s", e)
        raise ConnectionError(
            f"Cannot download ViAMR-v1.0 dataset: {e}"
        ) from e

    # The dataset stores one line per row. We need to reassemble
    # multi-line AMR blocks: #::snt line + AMR graph lines + blank line.
    train_data = dataset["train"]
    total_rows = len(train_data)

    logger.info(
        "Reassembling %d rows from ViAMR-v1.0...", total_rows
    )

    # Build indices
    concept_freq: Counter = Counter()
    relation_freq: Counter = Counter()
    concept_pairs: Counter = Counter()
    concept_to_relations: dict[str, Counter] = defaultdict(Counter)
    parsed_count = 0
    sentence_count = 0

    # State machine to reassemble AMR blocks from row-per-line format
    current_sentence = ""
    current_amr_lines: list[str] = []

    def _process_block() -> None:
        """Process a fully assembled sentence + AMR block."""
        nonlocal parsed_count, sentence_count

        if not current_amr_lines:
            return

        amr_string = "\n".join(current_amr_lines)

        # Validate balanced parentheses
        if amr_string.count("(") != amr_string.count(")"):
            return

        sentence_count += 1

        if max_samples is not None and sentence_count > max_samples:
            return

        _vi_amr_raw_entries.append({
            "sentence": current_sentence,
            "amr": amr_string,
        })

        try:
            graph = penman.decode(amr_string)
            _index_amr_graph(
                graph,
                concept_freq,
                relation_freq,
                concept_pairs,
                concept_to_relations,
            )
            parsed_count += 1
        except Exception:
            pass

    for i in range(total_rows):
        line = train_data[i].get("text", "")

        # Blank line = end of current block
        if not line or not line.strip():
            _process_block()
            current_sentence = ""
            current_amr_lines = []
            if max_samples is not None and sentence_count >= max_samples:
                break
            continue

        # Sentence metadata line
        snt_match = re.match(r"#\s*::snt\s+(.*)", line)
        if snt_match:
            # If we have a pending block, process it first
            if current_amr_lines:
                _process_block()
                current_amr_lines = []
            current_sentence = snt_match.group(1).strip()
            continue

        # Skip other metadata/comment lines
        if line.startswith("#"):
            continue

        # AMR graph content line
        current_amr_lines.append(line)

    # Process the last block if any
    if current_amr_lines:
        _process_block()

    _vi_amr_index = {
        "concept_freq": concept_freq,
        "relation_freq": relation_freq,
        "concept_pairs": concept_pairs,
        "concept_to_relations": dict(concept_to_relations),
        "total_graphs": parsed_count,
        "total_sentences": sentence_count,
    }

    logger.info(
        "ViAMR index built: %d graphs parsed, %d unique concepts, "
        "%d unique relations, %d concept pairs.",
        parsed_count,
        len(concept_freq),
        len(relation_freq),
        len(concept_pairs),
    )

    return _vi_amr_index


def _parse_viamr_entry(text: str) -> Optional[tuple[str, str]]:
    """Parse a single ViAMR dataset entry into sentence and AMR string.

    The ViAMR format follows standard AMR text format:
        # ::snt <Vietnamese sentence>
        (x / concept ...)

    Args:
        text: Raw text content from the dataset entry.

    Returns:
        A tuple of (sentence, amr_string), or None if parsing fails.
    """
    if not text or not text.strip():
        return None

    sentence = ""
    amr_lines = []
    in_amr = False

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Extract sentence from metadata
        snt_match = re.match(r"#\s*::snt\s+(.*)", line)
        if snt_match:
            sentence = snt_match.group(1).strip()
            continue

        # Skip other metadata lines
        if line.startswith("#"):
            continue

        # AMR graph content (starts with '(' or continues from previous)
        if line.startswith("(") or in_amr:
            amr_lines.append(line)
            in_amr = True

    if not amr_lines:
        return None

    amr_string = "\n".join(amr_lines)

    # Basic validation: must have balanced parentheses
    if amr_string.count("(") != amr_string.count(")"):
        return None

    return sentence, amr_string


def _index_amr_graph(
    graph: PenmanGraph,
    concept_freq: Counter,
    relation_freq: Counter,
    concept_pairs: Counter,
    concept_to_relations: dict[str, Counter],
) -> None:
    """Index a single AMR graph into the frequency counters.

    Args:
        graph: A parsed penman.Graph object.
        concept_freq: Counter to update with concept occurrences.
        relation_freq: Counter to update with relation occurrences.
        concept_pairs: Counter to update with (src, rel, tgt) triples.
        concept_to_relations: Dict to update with concept-relation mappings.
    """
    # Build variable -> concept mapping
    var_to_concept: dict[str, str] = {}
    for instance in graph.instances():
        concept = instance.target
        var_to_concept[instance.source] = concept
        concept_freq[concept] += 1

    # Index edges
    for edge in graph.edges():
        source_concept = var_to_concept.get(edge.source, edge.source)
        target_concept = var_to_concept.get(edge.target, edge.target)
        relation = edge.role

        relation_freq[relation] += 1
        concept_pairs[(source_concept, relation, target_concept)] += 1
        concept_to_relations[source_concept][relation] += 1
        concept_to_relations[target_concept][relation] += 1


def get_concept_frequency(concept: str) -> int:
    """Get the frequency of a concept in the Vietnamese AMR corpus.

    Args:
        concept: The AMR concept name to look up.

    Returns:
        The number of times this concept appears in the corpus.
        Returns 0 if the index is not loaded or concept not found.
    """
    if _vi_amr_index is None:
        return 0
    return _vi_amr_index["concept_freq"].get(concept, 0)


def get_relation_frequency(relation: str) -> int:
    """Get the frequency of a relation type in the Vietnamese AMR corpus.

    Args:
        relation: The AMR relation label (e.g., ':ARG0').

    Returns:
        The number of times this relation appears in the corpus.
        Returns 0 if the index is not loaded or relation not found.
    """
    if _vi_amr_index is None:
        return 0
    return _vi_amr_index["relation_freq"].get(relation, 0)


def get_concept_pair_frequency(
    source: str, relation: str, target: str
) -> int:
    """Get the frequency of a specific (concept, relation, concept) triple.

    Args:
        source: The source concept name.
        relation: The AMR relation type.
        target: The target concept name.

    Returns:
        The number of times this exact triple appears in the corpus.
    """
    if _vi_amr_index is None:
        return 0
    return _vi_amr_index["concept_pairs"].get(
        (source, relation, target), 0
    )


def get_common_relations_for_concept(
    concept: str, top_n: int = 10
) -> list[tuple[str, int]]:
    """Get the most common AMR relations for a given concept.

    Args:
        concept: The AMR concept to look up.
        top_n: Number of top relations to return.

    Returns:
        A list of (relation, count) tuples sorted by frequency.
    """
    if _vi_amr_index is None:
        return []
    relations = _vi_amr_index["concept_to_relations"].get(concept)
    if relations is None:
        return []
    return relations.most_common(top_n)


def find_similar_sentences(
    query: str,
    top_n: int = 5,
) -> list[dict[str, str]]:
    """Find Vietnamese sentences from the corpus similar to a query.

    Uses simple keyword overlap matching. For production use,
    consider replacing with embedding-based similarity.

    Args:
        query: The query string (Vietnamese or keywords).
        top_n: Number of results to return.

    Returns:
        A list of dicts with 'sentence' and 'amr' keys.
    """
    if not _vi_amr_raw_entries:
        return []

    query_tokens = set(query.lower().split())

    scored: list[tuple[float, dict[str, str]]] = []
    for entry in _vi_amr_raw_entries:
        sentence = entry["sentence"]
        sentence_tokens = set(sentence.lower().split())
        overlap = len(query_tokens & sentence_tokens)

        if overlap > 0:
            score = overlap / max(len(query_tokens), 1)
            scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [entry for _, entry in scored[:top_n]]


def get_index_stats() -> dict[str, int]:
    """Get summary statistics about the loaded ViAMR index.

    Returns:
        A dictionary with keys: total_graphs, total_sentences,
        unique_concepts, unique_relations, unique_pairs.
        Returns empty dict if index is not loaded.
    """
    if _vi_amr_index is None:
        return {}
    return {
        "total_graphs": _vi_amr_index["total_graphs"],
        "total_sentences": _vi_amr_index["total_sentences"],
        "unique_concepts": len(_vi_amr_index["concept_freq"]),
        "unique_relations": len(_vi_amr_index["relation_freq"]),
        "unique_pairs": len(_vi_amr_index["concept_pairs"]),
    }
