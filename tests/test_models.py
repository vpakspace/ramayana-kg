"""Tests for domain models."""

from ramayana_kg.models import (
    EntityType,
    ExtractedEntity,
    ExtractedRelationship,
    GraphContext,
    QAResult,
    RelationshipType,
    SearchResult,
    Verse,
)


def test_verse_creation():
    v = Verse(kanda="Bala Kanda", kanda_num=1, sarga=5, verse_num=10, text="Test verse")
    assert v.verse_id == "K1_S5_V10"
    assert v.kanda == "Bala Kanda"


def test_verse_custom_id():
    v = Verse(kanda="Bala Kanda", kanda_num=1, sarga=1, verse_num=1, text="Test", verse_id="custom")
    assert v.verse_id == "custom"


def test_entity_types():
    assert EntityType.CHARACTER == "Character"
    assert EntityType.LOCATION == "Location"
    assert EntityType.WEAPON == "Weapon"
    assert EntityType.EVENT == "Event"
    assert EntityType.CONCEPT == "Concept"


def test_relationship_types():
    assert RelationshipType.FATHER_OF == "FATHER_OF"
    assert RelationshipType.SPOUSE_OF == "SPOUSE_OF"
    assert RelationshipType.KILLS == "KILLS"
    assert RelationshipType.KIDNAPS == "KIDNAPS"
    assert RelationshipType.RESCUES == "RESCUES"


def test_extracted_entity():
    e = ExtractedEntity(name="Rama", entity_type=EntityType.CHARACTER, description="Hero")
    assert e.name == "Rama"
    assert e.confidence == 1.0
    assert e.verse_id == ""


def test_extracted_relationship():
    r = ExtractedRelationship(
        source="Rama", target="Ravana", rel_type=RelationshipType.KILLS
    )
    assert r.source == "Rama"
    assert r.target == "Ravana"
    assert r.confidence == 1.0


def test_graph_context():
    ctx = GraphContext()
    assert ctx.entities == []
    assert ctx.relationships == []
    assert ctx.paths == []
    assert ctx.source_verses == []


def test_search_result():
    sr = SearchResult(verse_id="K1_S1_V1", text="Test", score=0.95)
    assert sr.score == 0.95
    assert sr.kanda == ""
    assert sr.sarga == 0


def test_qa_result():
    result = QAResult(answer="Rama is the hero", mode="hybrid", confidence=0.8)
    assert result.answer == "Rama is the hero"
    assert result.sources == []
    assert result.graph_context is None


def test_qa_result_with_sources():
    src = SearchResult(verse_id="K1_S1_V1", text="verse text", score=0.9)
    ctx = GraphContext(entities=[{"name": "Rama"}])
    result = QAResult(
        answer="Answer",
        sources=[src],
        graph_context=ctx,
        mode="vector",
        confidence=0.85,
    )
    assert len(result.sources) == 1
    assert result.graph_context.entities[0]["name"] == "Rama"
