"""Pydantic data models for Phase 3 — Cultural Localization & Butterfly Effect.

Defines all structured data types used across the AMR-based energy delta
pipeline, including entity nodes, localization proposals, conflict reports,
and validation results.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Enumeration of supported entity categories in the localization pipeline."""

    CHARACTER = "character"
    LOCATION = "location"
    OBJECT = "object"
    WEATHER_ENTITY = "weather_entity"
    EVENT = "event"
    VEHICLE = "vehicle"
    FOOD = "food"
    CLOTHING = "clothing"
    ANIMAL = "animal"
    OTHER = "other"


class ValidationStatus(str, Enum):
    """Outcome status of a butterfly effect validation check."""

    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class EntityContext(BaseModel):
    """A single occurrence of an entity within a specific page context.

    Attributes:
        page: The page number where the entity appears.
        sentence: The full sentence containing the entity mention.
    """

    page: int
    sentence: str


class EntityNode(BaseModel):
    """A node in the global entity graph representing a cultural entity.

    Attributes:
        type: The semantic category of the entity.
        pages: List of page numbers where this entity appears.
        related: List of entity names that are semantically related.
        contexts: List of contextual sentence occurrences.
    """

    type: EntityType
    pages: list[int]
    related: list[str] = Field(default_factory=list)
    contexts: list[EntityContext] = Field(default_factory=list)


class LocalizationProposal(BaseModel):
    """A proposal to replace a Western cultural entity with a localized one.

    Attributes:
        proposal_id: Unique identifier for this proposal.
        original: The original entity name to be replaced.
        proposed: The proposed localized replacement.
        affected_pages: Pages where the replacement would take effect.
        rationale: Human-readable explanation for the substitution.
    """

    proposal_id: str
    original: str
    proposed: str
    affected_pages: list[int]
    rationale: str


class ButterflyConflict(BaseModel):
    """A detected semantic conflict from a localization proposal.

    Attributes:
        entity: The entity node where the conflict was detected.
        pages: Pages affected by the conflict.
        reason: Human-readable explanation of the conflict.
        delta_energy: The energy delta value that triggered the conflict.
    """

    entity: str
    pages: list[int]
    reason: str
    delta_energy: float


class EnergyEdge(BaseModel):
    """Energy measurement between two adjacent nodes in the AMR graph.

    Attributes:
        source: The source concept name.
        target: The target concept name.
        relation: The AMR relation type connecting source to target.
        energy: The computed energy value for this edge.
        breakdown: Detailed breakdown of energy by contributing factor.
    """

    source: str
    target: str
    relation: str
    energy: float
    breakdown: dict[str, float] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Complete result of a butterfly effect validation check.

    Attributes:
        status: ACCEPT or REJECT.
        total_delta_energy: Sum of all energy deltas across traversed edges.
        conflicts: List of detected semantic conflicts.
        energy_details: Detailed energy measurements for all evaluated edges.
    """

    status: ValidationStatus
    total_delta_energy: float
    conflicts: list[ButterflyConflict] = Field(default_factory=list)
    energy_details: list[EnergyEdge] = Field(default_factory=list)


class AMRNodeInfo(BaseModel):
    """Information about a single node in an AMR graph.

    Attributes:
        variable: The variable name assigned in the AMR graph (e.g., 'b').
        concept: The concept label (e.g., 'boy').
    """

    variable: str
    concept: str


class AMREdgeInfo(BaseModel):
    """Information about a labeled edge in an AMR graph.

    Attributes:
        source: The variable name of the source node.
        relation: The AMR relation type (e.g., ':ARG0', ':location').
        target: The variable name of the target node.
    """

    source: str
    relation: str
    target: str


class GlobalMetadata(BaseModel):
    """Immutable project constraints and configuration."""

    source_language: str = "EN"
    target_language: str = "vi"
    license_status: bool = True
    author_attribution: str = ""
    integrity_protection: bool = True
    adaptation_rights: bool = False
    translation_fidelity: str = "Strict"
    plot_alteration: bool = False
    cultural_localization: bool = False
    preserve_main_names: bool = True
    protected_names: list[str] = Field(default_factory=list)
    no_retouching: bool = True
    lock_character_color: bool = True
    never_change_rules: list[str] = Field(default_factory=list)
    style_register: str = "general"
    target_age_tone: int = 15
    glossary_strict_mode: bool = False
    sfx_handling: str = "In_panel_subs"
    satisfaction_clause: bool = False
    allow_bg_edit: bool = True
    max_drift_ratio: float = 0.15
    
    # Legacy field for backward compatibility if needed
    cultural_context: str = "Vietnam"

    model_config = {"extra": "allow"}


class Phase3InputPayload(BaseModel):
    """The incoming payload structure for the Phase 3 worker."""

    thread_id: str
    webhook_url: str | None = None
    global_metadata: GlobalMetadata
    source_pdf_path: str = ""
    output_phase_2: dict[str, Any] | None = None
    output_phase_1: list[dict[str, Any]] | None = None
    verified_text_pack: dict[str, Any] | None = None
    qa_feedback: dict[str, Any] | None = None
    use_llm: bool = True

    model_config = {"extra": "allow"}
