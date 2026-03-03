"""Tests for Cypher query library (mocked Neo4j)."""

from unittest.mock import MagicMock

from ramayana_kg.graph.queries import (
    character_profile,
    co_occurrence,
    family_tree,
    get_entity_relationships,
    get_entity_verses,
    search_entities,
    shortest_path,
)


def _mock_driver_with_result(records):
    """Create mock driver that returns specified records."""
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__ = MagicMock(return_value=session)
    driver.session.return_value.__exit__ = MagicMock(return_value=False)

    result = MagicMock()
    result.single.return_value = records[0] if records else None
    result.__iter__ = MagicMock(return_value=iter(records))
    session.run.return_value = result
    return driver, session


def test_character_profile_found():
    record = {
        "name": "Rama",
        "description": "Prince of Ayodhya",
        "outgoing": [{"type": "SPOUSE_OF", "target": "Sita"}],
    }
    incoming_record = {
        "incoming": [{"type": "SERVES", "source": "Hanuman"}],
    }
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__ = MagicMock(return_value=session)
    driver.session.return_value.__exit__ = MagicMock(return_value=False)

    result1 = MagicMock()
    result1.single.return_value = record
    result2 = MagicMock()
    result2.single.return_value = incoming_record
    session.run.side_effect = [result1, result2]

    profile = character_profile(driver, "Rama")
    assert profile["name"] == "Rama"
    assert len(profile["outgoing"]) == 1


def test_character_profile_not_found():
    driver, session = _mock_driver_with_result([])
    result = MagicMock()
    result.single.return_value = None
    session.run.return_value = result

    profile = character_profile(driver, "Unknown")
    assert profile == {}


def test_family_tree():
    record = {
        "name": "Rama",
        "family_out": [{"rel": "SPOUSE_OF", "name": "Sita"}],
        "family_in": [{"rel": "FATHER_OF", "name": "Dasaratha"}],
    }
    driver, session = _mock_driver_with_result([record])
    family = family_tree(driver, "Rama")
    assert len(family) == 2


def test_family_tree_empty():
    record = {"name": "Unknown", "family_out": [], "family_in": []}
    driver, session = _mock_driver_with_result([record])
    result = MagicMock()
    result.single.return_value = record
    session.run.return_value = result
    family = family_tree(driver, "Unknown")
    assert family == []


def test_shortest_path_found():
    record = {
        "path_names": ["Rama", "Sita", "Ravana"],
        "rel_types": ["SPOUSE_OF", "KIDNAPS"],
    }
    driver, session = _mock_driver_with_result([record])
    path = shortest_path(driver, "Rama", "Ravana")
    assert len(path) == 2
    assert "Rama" in path[0]


def test_shortest_path_not_found():
    driver, session = _mock_driver_with_result([])
    result = MagicMock()
    result.single.return_value = None
    session.run.return_value = result
    path = shortest_path(driver, "A", "B")
    assert path == []


def test_co_occurrence():
    records = [
        {"char1": "Rama", "char2": "Sita", "co_count": 50},
        {"char1": "Rama", "char2": "Lakshmana", "co_count": 45},
    ]
    driver, session = _mock_driver_with_result(records)
    result_mock = MagicMock()
    result_mock.__iter__ = MagicMock(return_value=iter(records))
    session.run.return_value = result_mock

    pairs = co_occurrence(driver, top_n=10)
    assert len(pairs) == 2
    assert pairs[0]["char1"] == "Rama"


def test_search_entities():
    records = [
        {"name": "Rama", "label": "Character", "description": "Hero", "score": 0.95},
    ]
    driver, session = _mock_driver_with_result(records)
    result_mock = MagicMock()
    result_mock.__iter__ = MagicMock(return_value=iter(records))
    session.run.return_value = result_mock

    results = search_entities(driver, "Rama", limit=5)
    assert len(results) == 1


def test_get_entity_verses():
    records = [
        {"verse_id": "K1_S1_V1", "text": "Rama went", "kanda_num": 1, "sarga": 1},
    ]
    driver, session = _mock_driver_with_result(records)
    result_mock = MagicMock()
    result_mock.__iter__ = MagicMock(return_value=iter(records))
    session.run.return_value = result_mock

    verses = get_entity_verses(driver, "Rama", limit=5)
    assert len(verses) == 1


def test_get_entity_relationships():
    outgoing_records = [
        {"rel_type": "SPOUSE_OF", "target": "Sita", "description": "Wife"},
    ]
    incoming_records = [
        {"rel_type": "FATHER_OF", "source": "Dasaratha", "description": "Father"},
    ]
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__ = MagicMock(return_value=session)
    driver.session.return_value.__exit__ = MagicMock(return_value=False)

    out_result = MagicMock()
    out_result.__iter__ = MagicMock(return_value=iter(outgoing_records))
    in_result = MagicMock()
    in_result.__iter__ = MagicMock(return_value=iter(incoming_records))
    session.run.side_effect = [out_result, in_result]

    rels = get_entity_relationships(driver, "Rama")
    assert len(rels) == 2
