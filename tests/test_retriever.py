"""Tests for hybrid retriever (mocked dependencies)."""

from unittest.mock import MagicMock, patch

from ramayana_kg.models import GraphContext, SearchResult
from ramayana_kg.rag.retriever import retrieve_graph, retrieve_hybrid, retrieve_vector


@patch("ramayana_kg.rag.retriever.vector_search")
def test_retrieve_vector(mock_vs):
    mock_vs.return_value = [
        {"verse_id": "K1_S1_V1", "text": "Rama went", "score": 0.9, "kanda_num": 1, "sarga": 1},
        {"verse_id": "K1_S1_V2", "text": "Sita followed", "score": 0.8, "kanda_num": 1, "sarga": 1},
    ]
    driver = MagicMock()
    results = retrieve_vector(driver, "Who is Rama?")
    assert len(results) == 2
    assert isinstance(results[0], SearchResult)
    assert results[0].score == 0.9


@patch("ramayana_kg.rag.retriever.search_entities")
def test_retrieve_graph(mock_search):
    mock_search.return_value = [
        {"name": "Rama", "label": "Character", "description": "Hero"},
    ]
    driver = MagicMock()

    with patch("ramayana_kg.rag.retriever.get_entity_relationships") as mock_rels, \
         patch("ramayana_kg.rag.retriever.get_entity_verses") as mock_verses:
        mock_rels.return_value = [{"type": "SPOUSE_OF", "direction": "->", "other": "Sita"}]
        mock_verses.return_value = [{"text": "Rama went to the forest"}]

        ctx = retrieve_graph(driver, "Who is Rama?")
        assert isinstance(ctx, GraphContext)
        assert len(ctx.entities) == 1
        assert ctx.entities[0]["name"] == "Rama"


@patch("ramayana_kg.rag.retriever.search_entities")
def test_retrieve_graph_empty(mock_search):
    mock_search.return_value = []
    driver = MagicMock()
    ctx = retrieve_graph(driver, "Unknown query")
    assert ctx.entities == []


@patch("ramayana_kg.rag.retriever.retrieve_graph")
@patch("ramayana_kg.rag.retriever.retrieve_vector")
def test_retrieve_hybrid(mock_vector, mock_graph):
    mock_vector.return_value = [
        SearchResult(verse_id="K1_S1_V1", text="Rama is the prince", score=0.85),
    ]
    mock_graph.return_value = GraphContext(
        entities=[{"name": "Rama", "label": "Character"}],
    )
    driver = MagicMock()

    with patch("ramayana_kg.rag.retriever.character_profile") as mock_profile:
        mock_profile.return_value = {
            "name": "Rama",
            "outgoing": [{"type": "SPOUSE_OF", "target": "Sita"}],
            "incoming": [],
        }
        results, ctx = retrieve_hybrid(driver, "Who is Rama?", client=MagicMock())
        assert len(results) >= 1
        assert ctx.entities[0]["name"] == "Rama"
