"""Cross-lingual AMR energy comparison for Butterfly Effect validation.

Computes energy delta by comparing the AMR graph structure of the
original English text against the localized Vietnamese text. This
eliminates the English-only limitation by using both amrlib (English)
and ViAMR corpus data (Vietnamese) to measure structural divergence.

The cross-lingual energy formula adds a new factor:

    E_cross(u, v) = E_base(u, v) + w_vi × VietnameseCorpusFactor(u, v)

Where VietnameseCorpusFactor leverages concept/relation frequencies
from the ViAMR-v1.0 dataset to assess how natural a concept pairing
is in Vietnamese AMR graphs.
"""

import logging
import math
from typing import Any, Optional

import penman
from penman import Graph as PenmanGraph

from .energy import (
    compute_edge_energy,
    compute_role_weight,
    load_config,
)
from .models import EnergyEdge
from .vi_amr_loader import (
    get_concept_frequency,
    get_concept_pair_frequency,
    get_index_stats,
    get_relation_frequency,
)

logger = logging.getLogger(__name__)

_CONFIG = load_config()

# Weight for Vietnamese corpus factor in cross-lingual energy
W_VI_CORPUS: float = 0.20

# Reduce other weights proportionally when Vietnamese factor is active
_CROSS_LINGUAL_SCALE: float = 1.0 - W_VI_CORPUS


def compute_vi_corpus_factor(
    source_concept: str,
    target_concept: str,
    relation: str,
) -> float:
    """Compute the Vietnamese corpus familiarity factor.

    Measures how natural a (concept, relation, concept) triple is
    in the Vietnamese AMR corpus. High frequency = natural pairing,
    low frequency = potentially awkward or semantically unusual.

    The factor combines:
        - Individual concept frequencies (are these concepts common?)
        - Pair frequency (does this exact pairing appear?)
        - Relation context (is this relation common for these concepts?)

    Args:
        source_concept: The source concept in the AMR triple.
        target_concept: The target concept in the AMR triple.
        relation: The AMR relation connecting them.

    Returns:
        A float in [0, 1]. Higher = more natural in Vietnamese.
    """
    stats = get_index_stats()
    if not stats or stats.get("total_graphs", 0) == 0:
        return 0.5  # Neutral fallback when corpus is unavailable

    total_graphs = stats["total_graphs"]

    # Factor 1: Source concept familiarity
    src_freq = get_concept_frequency(source_concept)
    src_score = min(src_freq / max(total_graphs * 0.01, 1), 1.0)

    # Factor 2: Target concept familiarity
    tgt_freq = get_concept_frequency(target_concept)
    tgt_score = min(tgt_freq / max(total_graphs * 0.01, 1), 1.0)

    # Factor 3: Exact triple match (strongest signal)
    pair_freq = get_concept_pair_frequency(
        source_concept, relation, target_concept
    )
    pair_score = min(pair_freq / max(total_graphs * 0.001, 1), 1.0)

    # Factor 4: Relation frequency for these concepts
    rel_freq = get_relation_frequency(relation)
    rel_score = min(rel_freq / max(total_graphs * 0.05, 1), 1.0)

    # Weighted combination: pair match is most important
    factor = (
        0.15 * src_score
        + 0.15 * tgt_score
        + 0.50 * pair_score
        + 0.20 * rel_score
    )

    return round(factor, 6)


def compute_cross_lingual_edge_energy(
    source_concept: str,
    target_concept: str,
    relation: str,
    entity_graph: dict[str, dict],
    depth: int = 0,
) -> EnergyEdge:
    """Compute edge energy with cross-lingual Vietnamese corpus factor.

    Extends the base energy formula with a Vietnamese corpus familiarity
    factor. When the ViAMR index is loaded, this provides a more
    accurate energy measurement for Vietnamese localization.

    Formula:
        E_cross = scale * E_base + w_vi * ViCorpusFactor

    Args:
        source_concept: The source concept/entity name.
        target_concept: The target concept/entity name.
        relation: The AMR relation type.
        entity_graph: The global entity graph for page/occurrence data.
        depth: The depth from the AMR root.

    Returns:
        An EnergyEdge with energy value and detailed breakdown.
    """
    # Compute base energy (scaled down to make room for VI factor)
    base_edge = compute_edge_energy(
        source_concept, target_concept, relation, entity_graph, depth
    )
    scaled_base = base_edge.energy * _CROSS_LINGUAL_SCALE

    # Compute Vietnamese corpus factor
    vi_factor = compute_vi_corpus_factor(
        source_concept, target_concept, relation
    )
    vi_contribution = W_VI_CORPUS * vi_factor

    total_energy = round(scaled_base + vi_contribution, 6)

    # Build detailed breakdown
    breakdown = {}
    for key, value in base_edge.breakdown.items():
        breakdown[key] = round(value * _CROSS_LINGUAL_SCALE, 6)
    breakdown["vi_corpus_factor"] = round(vi_contribution, 6)

    return EnergyEdge(
        source=source_concept,
        target=target_concept,
        relation=relation,
        energy=total_energy,
        breakdown=breakdown,
    )


def compute_cross_lingual_delta_energy(
    original: str,
    proposed: str,
    neighbors: list[dict[str, str]],
    entity_graph: dict[str, dict],
    depth_map: dict[str, int] | None = None,
) -> tuple[float, list[EnergyEdge], list[EnergyEdge]]:
    """Compute cross-lingual delta energy between original and proposed entity.

    Similar to compute_delta_energy() but uses the cross-lingual
    energy formula that includes Vietnamese corpus familiarity.

    The key insight: if the proposed Vietnamese entity has strong
    corpus support (high ViCorpusFactor), the delta energy is reduced
    because the substitution is more natural in Vietnamese.

    Args:
        original: The original entity being replaced.
        proposed: The proposed Vietnamese replacement.
        neighbors: List of neighbor dicts with 'concept' and 'relation'.
        entity_graph: The global entity graph.
        depth_map: Optional mapping of neighbor concepts to depths.

    Returns:
        A tuple of (delta_energy, original_edges, proposed_edges).
    """
    if depth_map is None:
        depth_map = {}

    original_edges: list[EnergyEdge] = []
    proposed_edges: list[EnergyEdge] = []
    total_delta = 0.0

    for neighbor in neighbors:
        neighbor_concept = neighbor["concept"]
        relation = neighbor["relation"]
        depth = depth_map.get(neighbor_concept, 1)

        # Cross-lingual energy with original entity
        e_original = compute_cross_lingual_edge_energy(
            original, neighbor_concept, relation, entity_graph, depth
        )
        original_edges.append(e_original)

        # Cross-lingual energy with proposed entity
        e_proposed = compute_cross_lingual_edge_energy(
            proposed, neighbor_concept, relation, entity_graph, depth
        )
        proposed_edges.append(e_proposed)

        total_delta += abs(e_original.energy - e_proposed.energy)

    return round(total_delta, 6), original_edges, proposed_edges


def compare_amr_structures(
    english_amr: str,
    vietnamese_amr: str,
) -> dict[str, Any]:
    """Compare two AMR graph structures for structural divergence.

    Analyzes the similarity between an English source AMR and a
    Vietnamese target AMR to detect semantic shifts introduced by
    localization. Uses triple overlap (similar to Smatch).

    Args:
        english_amr: AMR graph string for the English source text.
        vietnamese_amr: AMR graph string for the Vietnamese target text.

    Returns:
        A dictionary with:
            - 'shared_concepts': Concepts present in both graphs
            - 'en_only_concepts': Concepts only in English AMR
            - 'vi_only_concepts': Concepts only in Vietnamese AMR
            - 'shared_relations': Relation types used in both
            - 'structural_similarity': Float in [0, 1]
            - 'divergence_score': Float in [0, 1] (inverse of similarity)
    """
    try:
        en_graph = penman.decode(english_amr)
        vi_graph = penman.decode(vietnamese_amr)
    except Exception as e:
        logger.warning("Failed to decode AMR for comparison: %s", e)
        return {
            "shared_concepts": set(),
            "en_only_concepts": set(),
            "vi_only_concepts": set(),
            "shared_relations": set(),
            "structural_similarity": 0.0,
            "divergence_score": 1.0,
        }

    # Extract concept sets
    en_concepts = {inst.target for inst in en_graph.instances()}
    vi_concepts = {inst.target for inst in vi_graph.instances()}

    shared_concepts = en_concepts & vi_concepts
    en_only = en_concepts - vi_concepts
    vi_only = vi_concepts - en_concepts

    # Extract relation sets
    en_relations = {edge.role for edge in en_graph.edges()}
    vi_relations = {edge.role for edge in vi_graph.edges()}
    shared_relations = en_relations & vi_relations

    # Compute triple-level similarity (simplified Smatch)
    en_triples = set()
    en_var_to_concept = {
        inst.source: inst.target for inst in en_graph.instances()
    }
    for edge in en_graph.edges():
        src = en_var_to_concept.get(edge.source, edge.source)
        tgt = en_var_to_concept.get(edge.target, edge.target)
        en_triples.add((src, edge.role, tgt))

    vi_triples = set()
    vi_var_to_concept = {
        inst.source: inst.target for inst in vi_graph.instances()
    }
    for edge in vi_graph.edges():
        src = vi_var_to_concept.get(edge.source, edge.source)
        tgt = vi_var_to_concept.get(edge.target, edge.target)
        vi_triples.add((src, edge.role, tgt))

    shared_triples = en_triples & vi_triples
    total_triples = en_triples | vi_triples

    if total_triples:
        similarity = len(shared_triples) / len(total_triples)
    else:
        similarity = 1.0 if not en_triples and not vi_triples else 0.0

    return {
        "shared_concepts": shared_concepts,
        "en_only_concepts": en_only,
        "vi_only_concepts": vi_only,
        "shared_relations": shared_relations,
        "structural_similarity": round(similarity, 4),
        "divergence_score": round(1.0 - similarity, 4),
    }
