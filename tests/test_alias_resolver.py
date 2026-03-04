"""Tests for alias resolution and entity deduplication."""

import json
import tempfile
from pathlib import Path

from ramayana_kg.extraction.alias_resolver import (
    build_alias_index,
    load_seed_characters,
    resolve_entities,
    resolve_name,
)
from ramayana_kg.models import EntityType, ExtractedEntity


def test_load_seed_characters():
    seed = load_seed_characters()
    assert "Rama" in seed
    assert "Sita" in seed
    assert isinstance(seed["Rama"], list)


def test_load_seed_characters_missing_file():
    result = load_seed_characters("/nonexistent/path.json")
    assert result == {}


def test_build_alias_index():
    seed = {"Rama": ["Ram", "Ramachandra"], "Sita": ["Vaidehi"]}
    index = build_alias_index(seed)
    assert index["rama"] == "Rama"
    assert index["ram"] == "Rama"
    assert index["ramachandra"] == "Rama"
    assert index["vaidehi"] == "Sita"


def test_resolve_name_exact():
    index = {"rama": "Rama", "ram": "Rama"}
    assert resolve_name("Rama", index) == "Rama"
    assert resolve_name("Ram", index) == "Rama"
    assert resolve_name("RAMA", index) == "Rama"


def test_resolve_name_unknown():
    index = {"rama": "Rama"}
    result = resolve_name("CompletelyUnknown", index)
    assert result == "Completelyunknown"


def test_resolve_entities_deduplicates():
    entities = [
        ExtractedEntity(name="Rama", entity_type=EntityType.CHARACTER, description="Hero"),
        ExtractedEntity(name="Ram", entity_type=EntityType.CHARACTER, description="Prince"),
        ExtractedEntity(name="Ramachandra", entity_type=EntityType.CHARACTER, description="Avatar"),
    ]
    resolved = resolve_entities(entities)
    rama_entities = [e for e in resolved if e.name == "Rama"]
    assert len(rama_entities) == 1
    assert "Hero" in rama_entities[0].description


def test_resolve_entities_preserves_types():
    entities = [
        ExtractedEntity(name="Rama", entity_type=EntityType.CHARACTER),
        ExtractedEntity(name="Lanka", entity_type=EntityType.LOCATION),
    ]
    resolved = resolve_entities(entities)
    names = {e.name for e in resolved}
    assert "Rama" in names
    assert "Lanka" in names


def test_resolve_entities_merges_descriptions():
    entities = [
        ExtractedEntity(name="Rama", entity_type=EntityType.CHARACTER, description="Prince"),
        ExtractedEntity(
            name="Rama", entity_type=EntityType.CHARACTER,
            description="Avatar of Vishnu",
        ),
    ]
    resolved = resolve_entities(entities)
    assert len(resolved) == 1
    assert "Prince" in resolved[0].description
    assert "Avatar" in resolved[0].description


def test_resolve_entities_custom_seed():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([
            {"name": "TestHero", "aliases": ["TH", "Hero1"]},
        ], f)
        f.flush()

        entities = [
            ExtractedEntity(name="TH", entity_type=EntityType.CHARACTER),
            ExtractedEntity(name="Hero1", entity_type=EntityType.CHARACTER),
        ]
        resolved = resolve_entities(entities, seed_path=f.name)
        names = [e.name for e in resolved]
        assert "TestHero" in names

    Path(f.name).unlink()


def test_resolve_name_fuzzy_match():
    index = {"hanuman": "Hanuman", "hanumân": "Hanuman"}
    result = resolve_name("Hanumaan", index, threshold=0.7)
    assert result == "Hanuman"
