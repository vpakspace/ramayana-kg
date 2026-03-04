"""Tests for Neo4j schema management (mocked)."""

from unittest.mock import MagicMock

from ramayana_kg.graph.schema import (
    CONSTRAINTS,
    FULLTEXT_INDEXES,
    clear_database,
    create_schema,
    get_stats,
)


def _mock_driver():
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__ = MagicMock(return_value=session)
    driver.session.return_value.__exit__ = MagicMock(return_value=False)
    return driver, session


def test_create_schema():
    driver, session = _mock_driver()
    create_schema(driver)
    assert session.run.call_count == len(CONSTRAINTS) + len(FULLTEXT_INDEXES)


def test_clear_database():
    driver, session = _mock_driver()
    result_mock = MagicMock()
    result_mock.single.return_value = {"cnt": 42}
    session.run.return_value = result_mock

    count = clear_database(driver)
    assert count == 42


def test_clear_database_empty():
    driver, session = _mock_driver()
    result_mock = MagicMock()
    result_mock.single.return_value = {"cnt": 0}
    session.run.return_value = result_mock

    count = clear_database(driver)
    assert count == 0


def test_get_stats():
    driver, session = _mock_driver()

    nodes_result = MagicMock()
    nodes_result.single.return_value = {"cnt": 100}
    rels_result = MagicMock()
    rels_result.single.return_value = {"cnt": 200}
    labels_result = MagicMock()
    labels_result.__iter__ = MagicMock(return_value=iter([
        {"label": "Character", "cnt": 50},
        {"label": "Location", "cnt": 30},
    ]))
    rel_types_result = MagicMock()
    rel_types_result.__iter__ = MagicMock(return_value=iter([
        {"rel_type": "SPOUSE_OF", "cnt": 10},
    ]))
    session.run.side_effect = [nodes_result, rels_result, labels_result, rel_types_result]

    stats = get_stats(driver)
    assert stats["total_nodes"] == 100
    assert stats["total_relationships"] == 200
    assert stats["nodes_by_label"]["Character"] == 50


def test_constraints_count():
    assert len(CONSTRAINTS) == 8


def test_fulltext_indexes_count():
    assert len(FULLTEXT_INDEXES) == 2
