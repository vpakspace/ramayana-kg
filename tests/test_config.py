"""Tests for configuration."""

from ramayana_kg.config import Settings, settings


def test_settings_defaults():
    s = Settings(openai_api_key="test")
    assert s.embedding_model == "text-embedding-3-small"
    assert s.llm_model == "gpt-4o-mini"
    assert s.embedding_dimensions == 1536
    assert s.neo4j_database == "ramayana"


def test_settings_neo4j():
    s = Settings(openai_api_key="test", neo4j_uri="bolt://custom:7687")
    assert s.neo4j_uri == "bolt://custom:7687"
    assert s.neo4j_user == "neo4j"


def test_settings_extraction():
    s = Settings(openai_api_key="test")
    assert s.extraction_batch_size == 20
    assert s.alias_fuzzy_threshold == 0.85


def test_settings_retrieval():
    s = Settings(openai_api_key="test")
    assert s.top_k_vector == 20
    assert s.top_k_final == 5
    assert s.graph_depth == 2


def test_settings_generation():
    s = Settings(openai_api_key="test")
    assert s.temperature == 0.3
    assert s.max_context_tokens == 4000


def test_global_settings_instance():
    assert settings is not None
    assert isinstance(settings, Settings)
