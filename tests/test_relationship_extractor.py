"""Tests for relationship extraction."""

from unittest.mock import MagicMock

from ramayana_kg.extraction.relationship_extractor import (
    _parse_relationships,
    extract_relationships_batch,
)
from ramayana_kg.models import RelationshipType, Verse


def test_parse_relationships_valid():
    raw = (
        '[{"source": "Rama", "target": "Ravana",'
        ' "rel_type": "KILLS", "description": "In battle"}]'
    )
    verses = [Verse(kanda="Y", kanda_num=6, sarga=1, verse_num=1, text="t")]
    rels = _parse_relationships(raw, verses)
    assert len(rels) == 1
    assert rels[0].source == "Rama"
    assert rels[0].target == "Ravana"
    assert rels[0].rel_type == RelationshipType.KILLS


def test_parse_relationships_multiple():
    raw = """[
        {"source": "Ravana", "target": "Sita", "rel_type": "KIDNAPS"},
        {"source": "Rama", "target": "Sita", "rel_type": "RESCUES"},
        {"source": "Hanuman", "target": "Rama", "rel_type": "SERVES"}
    ]"""
    verses = [Verse(kanda="Y", kanda_num=6, sarga=1, verse_num=1, text="t")]
    rels = _parse_relationships(raw, verses)
    assert len(rels) == 3


def test_parse_relationships_invalid_type():
    raw = '[{"source": "A", "target": "B", "rel_type": "INVALID_TYPE"}]'
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    rels = _parse_relationships(raw, verses)
    assert len(rels) == 0


def test_parse_relationships_invalid_json():
    rels = _parse_relationships("bad json", [])
    assert rels == []


def test_parse_relationships_empty():
    rels = _parse_relationships("[]", [])
    assert rels == []


def test_parse_relationships_missing_fields():
    raw = '[{"source": "Rama"}, {"source": "A", "target": "B"}]'
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    rels = _parse_relationships(raw, verses)
    assert len(rels) == 0


def test_parse_relationships_markdown_fences():
    raw = '```json\n[{"source": "Rama", "target": "Sita", "rel_type": "SPOUSE_OF"}]\n```'
    verses = [Verse(kanda="B", kanda_num=1, sarga=1, verse_num=1, text="t")]
    rels = _parse_relationships(raw, verses)
    assert len(rels) == 1


def test_extract_relationships_batch_empty():
    result = extract_relationships_batch([], client=MagicMock())
    assert result == []


def test_extract_relationships_batch_calls_openai(sample_verses):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        '[{"source": "Rama", "target": "Sita",'
        ' "rel_type": "SPOUSE_OF"}]'
    )
    mock_client.chat.completions.create.return_value = mock_response

    rels = extract_relationships_batch(sample_verses[:2], client=mock_client)
    assert len(rels) >= 1
