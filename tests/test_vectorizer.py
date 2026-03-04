"""Tests for vector embeddings (mocked OpenAI)."""

from unittest.mock import MagicMock

from ramayana_kg.embeddings.vectorizer import embed_texts, vector_search


def _mock_openai_embeddings(dim=1536):
    client = MagicMock()
    response = MagicMock()
    item = MagicMock()
    item.embedding = [0.1] * dim
    response.data = [item]
    client.embeddings.create.return_value = response
    return client


def test_embed_texts_single():
    client = _mock_openai_embeddings()
    result = embed_texts(["Hello world"], client=client)
    assert len(result) == 1
    assert len(result[0]) == 1536
    client.embeddings.create.assert_called_once()


def test_embed_texts_empty():
    result = embed_texts([])
    assert result == []


def test_embed_texts_multiple():
    client = MagicMock()
    response = MagicMock()
    items = [MagicMock() for _ in range(3)]
    for item in items:
        item.embedding = [0.5] * 1536
    response.data = items
    client.embeddings.create.return_value = response

    result = embed_texts(["a", "b", "c"], client=client)
    assert len(result) == 3


def test_vector_search_calls_driver():
    client = _mock_openai_embeddings()
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__ = MagicMock(return_value=session)
    driver.session.return_value.__exit__ = MagicMock(return_value=False)

    records = [
        {"verse_id": "K1_S1_V1", "text": "Rama went", "score": 0.95, "kanda_num": 1, "sarga": 1},
    ]
    result_mock = MagicMock()
    result_mock.__iter__ = MagicMock(return_value=iter(records))
    session.run.return_value = result_mock

    results = vector_search(driver, "Rama", top_k=5, client=client)
    assert len(results) == 1
    assert results[0]["verse_id"] == "K1_S1_V1"
