"""Tests for graph builder (mocked Neo4j)."""

from unittest.mock import MagicMock

from ramayana_kg.graph.builder import (
    build_entity_nodes,
    build_relationships,
    build_structural_hierarchy,
)
from ramayana_kg.models import EntityType, ExtractedEntity, Verse


def _make_mock_driver():
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__ = MagicMock(return_value=session)
    driver.session.return_value.__exit__ = MagicMock(return_value=False)
    return driver, session


def test_build_structural_hierarchy_creates_kandas():
    driver, session = _make_mock_driver()
    verses = [
        Verse(kanda="Bala Kanda", kanda_num=1, sarga=1, verse_num=1, text="Text 1"),
        Verse(kanda="Bala Kanda", kanda_num=1, sarga=1, verse_num=2, text="Text 2"),
        Verse(kanda="Ayodhya Kanda", kanda_num=2, sarga=1, verse_num=1, text="Text 3"),
    ]
    build_structural_hierarchy(driver, verses)
    assert session.run.call_count > 0


def test_build_structural_hierarchy_empty():
    driver, session = _make_mock_driver()
    build_structural_hierarchy(driver, [])
    # No calls for empty verses (only session creation)


def test_build_entity_nodes(sample_entities):
    driver, session = _make_mock_driver()
    build_entity_nodes(driver, sample_entities)
    assert session.run.call_count > 0


def test_build_entity_nodes_empty():
    driver, session = _make_mock_driver()
    build_entity_nodes(driver, [])
    assert session.run.call_count == 0


def test_build_entity_nodes_with_verse_id():
    driver, session = _make_mock_driver()
    entities = [
        ExtractedEntity(name="Rama", entity_type=EntityType.CHARACTER, verse_id="K1_S1_V1"),
    ]
    build_entity_nodes(driver, entities)
    # Should call run twice: once for MERGE node, once for MENTIONED_IN
    assert session.run.call_count == 2


def test_build_relationships(sample_relationships):
    driver, session = _make_mock_driver()
    build_relationships(driver, sample_relationships)
    assert session.run.call_count == len(sample_relationships)


def test_build_relationships_empty():
    driver, session = _make_mock_driver()
    build_relationships(driver, [])
    assert session.run.call_count == 0
