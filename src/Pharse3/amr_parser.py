"""AMR graph construction using amrlib and penman.

Provides utilities to parse English sentences into Abstract Meaning
Representation (AMR) graphs and extract structured node/edge information
for energy-based butterfly effect analysis.

This module wraps the amrlib library (https://github.com/bjascob/amrlib)
and the penman library for graph manipulation. The AMR model is loaded
once and cached at module level for performance.
"""

import logging
from pathlib import Path
from typing import Optional

import amrlib
import penman
from penman import Graph as PenmanGraph

from .models import AMREdgeInfo, AMRNodeInfo

logger = logging.getLogger(__name__)

# Module-level cache for the loaded StoG model
_stog_model = None


def load_amr_model(model_dir: Optional[str] = None) -> None:
    """Load the amrlib Sentence-to-Graph (StoG) model into memory.

    The model is cached at module level to avoid repeated loading.
    On first call, downloads the default model if none is installed.

    Args:
        model_dir: Optional path to a pre-downloaded model directory.
            If None, uses the default amrlib model location.

    Raises:
        RuntimeError: If the model cannot be loaded or downloaded.
    """
    global _stog_model
    if _stog_model is not None:
        return

    try:
        if model_dir:
            _stog_model = amrlib.load_stog_model(model_dir=model_dir)
        else:
            _stog_model = amrlib.load_stog_model()
        logger.info("AMR StoG model loaded successfully.")
    except Exception as e:
        logger.warning(
            "Failed to load AMR model: %s", e
        )
        # Attempt auto-download to amrlib's default data dir
        try:
            data_dir = str(
                Path(amrlib.__file__).parent / "data"
            )
            logger.info(
                "Attempting model download to: %s", data_dir
            )
            amrlib.download_model("model_stog", data_dir)
            _stog_model = amrlib.load_stog_model()
            logger.info("AMR model downloaded and loaded successfully.")
        except Exception as download_err:
            raise RuntimeError(
                "AMR model not found. Please download manually:\n"
                "  1. Visit https://github.com/bjascob/amrlib-models\n"
                "  2. Download model_parse_xfm_bart_large-v0_1_0.tar.gz\n"
                "  3. Extract to: <python>/lib/site-packages/amrlib/data/\n"
                f"  Original error: {download_err}"
            ) from download_err


def parse_sentences_to_amr(sentences: list[str]) -> list[str]:
    """Parse a list of English sentences into AMR graph strings.

    Uses the loaded amrlib StoG model to convert natural language
    sentences into PENMAN-notation AMR graph strings.

    Args:
        sentences: A list of English sentences to parse.

    Returns:
        A list of AMR graph strings in PENMAN notation.
        Each string represents the semantic structure of a sentence.

    Raises:
        RuntimeError: If the AMR model has not been loaded.
    """
    if _stog_model is None:
        raise RuntimeError(
            "AMR model not loaded. Call load_amr_model() first."
        )

    graphs = _stog_model.parse_sents(sentences)
    logger.debug("Parsed %d sentences into AMR graphs.", len(graphs))
    return graphs


def decode_amr_string(amr_string: str) -> PenmanGraph:
    """Decode a PENMAN-notation AMR string into a structured graph.

    Args:
        amr_string: A single AMR graph in PENMAN string format.

    Returns:
        A penman.Graph object representing the AMR structure.

    Raises:
        penman.DecodeError: If the AMR string is malformed.
    """
    return penman.decode(amr_string)


def extract_amr_nodes(graph: PenmanGraph) -> list[AMRNodeInfo]:
    """Extract all concept nodes from an AMR graph.

    Each node in the AMR graph maps a variable to a concept label.
    For example, variable 'b' might map to concept 'boy'.

    Args:
        graph: A penman.Graph object.

    Returns:
        A list of AMRNodeInfo objects containing variable-concept pairs.
    """
    nodes = []
    for instance in graph.instances():
        nodes.append(
            AMRNodeInfo(variable=instance.source, concept=instance.target)
        )
    return nodes


def extract_amr_edges(graph: PenmanGraph) -> list[AMREdgeInfo]:
    """Extract all labeled edges (relations) from an AMR graph.

    Edges represent semantic relations between concepts, such as
    :ARG0 (agent), :ARG1 (patient), :location, :mod (modifier), etc.

    Args:
        graph: A penman.Graph object.

    Returns:
        A list of AMREdgeInfo objects with source, relation, and target.
    """
    edges = []
    for edge in graph.edges():
        edges.append(
            AMREdgeInfo(
                source=edge.source,
                relation=edge.role,
                target=edge.target,
            )
        )
    return edges


def build_adjacency_from_amr(
    graph: PenmanGraph,
) -> dict[str, list[dict[str, str]]]:
    """Build a bidirectional adjacency list from an AMR graph.

    Creates an adjacency mapping keyed by concept names (not variables).
    Each concept lists its neighbors along with the connecting AMR
    relation type. Both forward and reverse edges are included to
    enable full BFS/DFS traversal.

    Args:
        graph: A penman.Graph object.

    Returns:
        A dictionary mapping concept names to lists of neighbor info.
        Each neighbor entry contains 'concept' and 'relation' keys.

    Example:
        {
            "want-01": [
                {"concept": "boy", "relation": ":ARG0"},
                {"concept": "go-02", "relation": ":ARG1"}
            ],
            "boy": [
                {"concept": "want-01", "relation": ":ARG0-of"}
            ]
        }
    """
    # Build variable -> concept lookup
    var_to_concept: dict[str, str] = {}
    for instance in graph.instances():
        var_to_concept[instance.source] = instance.target

    adjacency: dict[str, list[dict[str, str]]] = {}

    for edge in graph.edges():
        source_concept = var_to_concept.get(edge.source, edge.source)
        target_concept = var_to_concept.get(edge.target, edge.target)

        # Forward edge: source -> target
        if source_concept not in adjacency:
            adjacency[source_concept] = []
        adjacency[source_concept].append({
            "concept": target_concept,
            "relation": edge.role,
        })

        # Reverse edge: target -> source (for bidirectional traversal)
        if target_concept not in adjacency:
            adjacency[target_concept] = []
        adjacency[target_concept].append({
            "concept": source_concept,
            "relation": f"{edge.role}-of",
        })

    return adjacency


def get_node_depth(graph: PenmanGraph, target_variable: str) -> int:
    """Calculate the depth of a node from the root in the AMR graph.

    Uses BFS from the graph root to find the shortest path length
    to the target variable.

    Args:
        graph: A penman.Graph object.
        target_variable: The variable name of the target node.

    Returns:
        The depth (number of edges from root to target).
        Returns 0 if the target is the root.
        Returns -1 if the variable is not found in the graph.
    """
    root = graph.top
    if target_variable == root:
        return 0

    # Build variable-level adjacency for BFS depth search
    var_adjacency: dict[str, list[str]] = {}
    for edge in graph.edges():
        if edge.source not in var_adjacency:
            var_adjacency[edge.source] = []
        var_adjacency[edge.source].append(edge.target)

    # BFS to find shortest path depth
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(root, 0)]

    while queue:
        current, depth = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        if current == target_variable:
            return depth

        for neighbor in var_adjacency.get(current, []):
            if neighbor not in visited:
                queue.append((neighbor, depth + 1))

    return -1
