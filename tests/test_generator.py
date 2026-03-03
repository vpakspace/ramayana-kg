"""Tests for answer generation (mocked dependencies)."""

from unittest.mock import MagicMock, patch

from ramayana_kg.models import GraphContext, QAResult, SearchResult
from ramayana_kg.rag.generator import format_graph_context, format_verse_passages, generate_answer


def test_format_verse_passages_empty():
    result = format_verse_passages([])
    assert "No relevant" in result


def test_format_verse_passages():
    results = [
        SearchResult(verse_id="K1_S1_V1", text="Rama went to forest", score=0.9),
        SearchResult(verse_id="K1_S1_V2", text="Sita followed", score=0.8),
    ]
    text = format_verse_passages(results)
    assert "K1_S1_V1" in text
    assert "0.900" in text
    assert "Rama went" in text


def test_format_graph_context_empty():
    ctx = GraphContext()
    result = format_graph_context(ctx)
    assert "No graph" in result


def test_format_graph_context_with_entities():
    ctx = GraphContext(
        entities=[{"name": "Rama", "label": "Character"}],
        paths=["Rama -[SPOUSE_OF]-> Sita"],
    )
    result = format_graph_context(ctx)
    assert "Rama" in result
    assert "SPOUSE_OF" in result


def test_format_graph_context_with_relationships():
    ctx = GraphContext(
        entities=[{"name": "Sita", "label": "Character"}],
        relationships=[{"type": "KIDNAPS", "direction": "<-", "other": "Ravana"}],
    )
    result = format_graph_context(ctx)
    assert "KIDNAPS" in result


@patch("ramayana_kg.rag.generator.retrieve_hybrid")
def test_generate_answer_hybrid(mock_hybrid):
    mock_hybrid.return_value = (
        [SearchResult(verse_id="K1_S1_V1", text="Rama is great", score=0.9)],
        GraphContext(entities=[{"name": "Rama", "label": "Character"}]),
    )

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Rama is the hero of Ramayana."
    mock_client.chat.completions.create.return_value = mock_response

    driver = MagicMock()
    result = generate_answer("Who is Rama?", driver, mode="hybrid", client=mock_client)
    assert isinstance(result, QAResult)
    assert "Rama" in result.answer
    assert result.mode == "hybrid"


@patch("ramayana_kg.rag.generator.retrieve_vector")
def test_generate_answer_vector_mode(mock_vector):
    mock_vector.return_value = [
        SearchResult(verse_id="K1_S1_V1", text="Rama went", score=0.85),
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Vector-based answer."
    mock_client.chat.completions.create.return_value = mock_response

    driver = MagicMock()
    result = generate_answer("query", driver, mode="vector", client=mock_client)
    assert result.mode == "vector"


@patch("ramayana_kg.rag.generator.retrieve_graph")
def test_generate_answer_graph_mode(mock_graph):
    mock_graph.return_value = GraphContext(
        entities=[{"name": "Rama", "label": "Character", "description": "Hero"}],
    )

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Graph-based answer."
    mock_client.chat.completions.create.return_value = mock_response

    driver = MagicMock()
    result = generate_answer("query", driver, mode="graph", client=mock_client)
    assert result.mode == "graph"
    assert result.confidence == 0.5  # graph-only default
