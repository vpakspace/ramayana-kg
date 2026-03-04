"""Tests for LLM entity extraction."""

from unittest.mock import MagicMock

from ramayana_kg.extraction.entity_extractor import _parse_entities, extract_entities_batch
from ramayana_kg.models import EntityType, Verse


def test_parse_entities_valid_json():
    raw = '[{"name": "Rama", "type": "Character", "description": "Hero of the epic"}]'
    verses = [Verse(kanda="Bala Kanda", kanda_num=1, sarga=1, verse_num=1, text="test")]
    entities = _parse_entities(raw, verses)
    assert len(entities) == 1
    assert entities[0].name == "Rama"
    assert entities[0].entity_type == EntityType.CHARACTER


def test_parse_entities_multiple():
    raw = """[
        {"name": "Rama", "type": "Character", "description": "Prince"},
        {"name": "Lanka", "type": "Location", "description": "Island"},
        {"name": "Brahmastra", "type": "Weapon", "description": "Divine weapon"}
    ]"""
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    entities = _parse_entities(raw, verses)
    assert len(entities) == 3
    assert entities[1].entity_type == EntityType.LOCATION
    assert entities[2].entity_type == EntityType.WEAPON


def test_parse_entities_with_markdown_fences():
    raw = '```json\n[{"name": "Sita", "type": "Character", "description": "Wife"}]\n```'
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    entities = _parse_entities(raw, verses)
    assert len(entities) == 1
    assert entities[0].name == "Sita"


def test_parse_entities_invalid_json():
    raw = "not json at all"
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    entities = _parse_entities(raw, verses)
    assert entities == []


def test_parse_entities_empty_array():
    raw = "[]"
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    entities = _parse_entities(raw, verses)
    assert entities == []


def test_parse_entities_invalid_type_fallback():
    raw = '[{"name": "Foo", "type": "InvalidType", "description": "unknown"}]'
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    entities = _parse_entities(raw, verses)
    assert len(entities) == 1
    assert entities[0].entity_type == EntityType.CHARACTER  # fallback


def test_parse_entities_skips_empty_names():
    raw = '[{"name": "", "type": "Character"}, {"name": "Rama", "type": "Character"}]'
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    entities = _parse_entities(raw, verses)
    assert len(entities) == 1


def test_parse_entities_default_verse_id():
    raw = '[{"name": "Rama", "type": "Character"}]'
    verses = [Verse(kanda="B", kanda_num=1, sarga=5, verse_num=3, text="t")]
    entities = _parse_entities(raw, verses)
    assert entities[0].verse_id == "K1_S5_V3"


def test_extract_entities_batch_calls_openai(sample_verses):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        '[{"name": "Rama", "type": "Character", "description": "Hero"}]'
    )
    mock_client.chat.completions.create.return_value = mock_response

    entities = extract_entities_batch(sample_verses[:2], client=mock_client)
    assert len(entities) >= 1
    mock_client.chat.completions.create.assert_called_once()


def test_extract_entities_batch_empty():
    result = extract_entities_batch([], client=MagicMock())
    assert result == []
