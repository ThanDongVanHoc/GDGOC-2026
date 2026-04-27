"""Unit tests for the dynamic prompt builder.

Verifies that each supported ``style_register`` value produces valid,
non-empty prompts containing the expected constraints and format
instructions.
"""

import sys
import os

import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.prompt_builder import (
    build_localization_system_prompt,
    build_scoring_system_prompt,
)
from core.models import GlobalMetadata


_SUPPORTED_STYLES = ["children_book", "manga", "novel", "academic", "general"]


class TestLocalizationPrompt:
    """Tests for ``build_localization_system_prompt``."""

    @pytest.mark.parametrize("style", _SUPPORTED_STYLES)
    def test_produces_non_empty_prompt(self, style: str) -> None:
        """Each style must produce a non-empty string."""
        metadata = GlobalMetadata(style_register=style)
        prompt = build_localization_system_prompt(metadata)
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    @pytest.mark.parametrize("style", _SUPPORTED_STYLES)
    def test_contains_json_format_instruction(self, style: str) -> None:
        """Every prompt must end with the JSON output format spec."""
        metadata = GlobalMetadata(style_register=style)
        prompt = build_localization_system_prompt(metadata)
        assert '"id"' in prompt
        assert '"localization"' in prompt

    def test_protected_names_injected(self) -> None:
        """Protected names from metadata must appear in the prompt."""
        metadata = GlobalMetadata(
            style_register="general",
            protected_names=["Harry", "Dumbledore"],
        )
        prompt = build_localization_system_prompt(metadata)
        assert "Harry" in prompt
        assert "Dumbledore" in prompt
        assert "NEVER rename" in prompt

    def test_never_change_rules_injected(self) -> None:
        """Never-change rules from metadata must appear in the prompt."""
        metadata = GlobalMetadata(
            style_register="general",
            never_change_rules=["Do not alter plot structure"],
        )
        prompt = build_localization_system_prompt(metadata)
        assert "Do not alter plot structure" in prompt

    def test_cultural_localization_disabled(self) -> None:
        """When cultural_localization is False, prompt must say so."""
        metadata = GlobalMetadata(
            style_register="children_book",
            cultural_localization=False,
        )
        prompt = build_localization_system_prompt(metadata)
        assert "DISABLED" in prompt

    def test_young_audience_tone(self) -> None:
        """target_age_tone <= 8 should produce 'very young' language."""
        metadata = GlobalMetadata(
            style_register="children_book",
            target_age_tone=6,
        )
        prompt = build_localization_system_prompt(metadata)
        assert "very young" in prompt.lower() or "under 8" in prompt

    def test_unknown_style_falls_back_to_general(self) -> None:
        """An unrecognized style_register value should use 'general'."""
        metadata = GlobalMetadata(style_register="unknown_xyz")
        prompt = build_localization_system_prompt(metadata)
        assert "balanced" in prompt.lower() or "neutral" in prompt.lower()


class TestScoringPrompt:
    """Tests for ``build_scoring_system_prompt``."""

    @pytest.mark.parametrize("style", _SUPPORTED_STYLES)
    def test_produces_non_empty_prompt(self, style: str) -> None:
        """Each style must produce a non-empty scoring prompt."""
        metadata = GlobalMetadata(style_register=style)
        prompt = build_scoring_system_prompt(metadata)
        assert isinstance(prompt, str)
        assert len(prompt) > 50

    @pytest.mark.parametrize("style", _SUPPORTED_STYLES)
    def test_contains_json_format_instruction(self, style: str) -> None:
        """Every scoring prompt must end with the JSON output spec."""
        metadata = GlobalMetadata(style_register=style)
        prompt = build_scoring_system_prompt(metadata)
        assert '"id"' in prompt
        assert '"score"' in prompt

    def test_children_book_mentions_holidays(self) -> None:
        """Children's book scoring should reference Western holidays."""
        metadata = GlobalMetadata(style_register="children_book")
        prompt = build_scoring_system_prompt(metadata)
        assert "Christmas" in prompt or "Halloween" in prompt

    def test_manga_mentions_japanese_culture(self) -> None:
        """Manga scoring should reference Japanese cultural elements."""
        metadata = GlobalMetadata(style_register="manga")
        prompt = build_scoring_system_prompt(metadata)
        assert "Japanese" in prompt or "bento" in prompt.lower()

    def test_unknown_style_falls_back_to_general(self) -> None:
        """An unrecognized style should fall back to general scoring."""
        metadata = GlobalMetadata(style_register="alien_style")
        prompt = build_scoring_system_prompt(metadata)
        assert "Cultural Context" in prompt or "cultural" in prompt.lower()
