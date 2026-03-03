"""Shared test fixtures for Ramayana KG tests."""

import os
import sys
import types

# Stub neo4j if not installed
if "neo4j" not in sys.modules:
    _neo4j = types.ModuleType("neo4j")

    class _FakeDriver:
        def session(self, **kw):
            return _FakeSession()
        def close(self):
            pass

    class _FakeSession:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def run(self, *a, **kw):
            return _FakeResult()

    class _FakeResult:
        def single(self):
            return None
        def __iter__(self):
            return iter([])

    _neo4j.Driver = _FakeDriver
    _neo4j.GraphDatabase = type("GraphDatabase", (), {"driver": staticmethod(lambda *a, **kw: _FakeDriver())})
    sys.modules["neo4j"] = _neo4j

# Stub openai if not installed
if "openai" not in sys.modules:
    _openai = types.ModuleType("openai")

    class _FakeOpenAI:
        def __init__(self, **kw):
            self.chat = type("chat", (), {"completions": type("c", (), {"create": staticmethod(lambda **kw: None)})})()
            self.embeddings = type("emb", (), {"create": staticmethod(lambda **kw: None)})()

    _openai.OpenAI = _FakeOpenAI
    sys.modules["openai"] = _openai

# Stub thefuzz
if "thefuzz" not in sys.modules:
    _thefuzz = types.ModuleType("thefuzz")
    _fuzz = types.ModuleType("thefuzz.fuzz")
    def _simple_ratio(a, b):
        """Simple sequence matcher ratio (0-100)."""
        from difflib import SequenceMatcher
        return int(SequenceMatcher(None, a, b).ratio() * 100)
    _fuzz.ratio = _simple_ratio
    _thefuzz.fuzz = _fuzz
    sys.modules["thefuzz"] = _thefuzz
    sys.modules["thefuzz.fuzz"] = _fuzz

# Stub httpx
if "httpx" not in sys.modules:
    _httpx = types.ModuleType("httpx")
    _httpx.get = lambda *a, **kw: None
    sys.modules["httpx"] = _httpx

# Set default env vars
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "test-password")
os.environ.setdefault("NEO4J_DATABASE", "ramayana")


import pytest

from ramayana_kg.models import (
    EntityType,
    ExtractedEntity,
    ExtractedRelationship,
    RelationshipType,
    Verse,
)


@pytest.fixture
def sample_verses():
    return [
        Verse(kanda="Bala Kanda", kanda_num=1, sarga=1, verse_num=1,
              text="The glorious Rama, son of Dasaratha, went to the forest with Sita and Lakshmana."),
        Verse(kanda="Bala Kanda", kanda_num=1, sarga=1, verse_num=2,
              text="The sage Vishvamitra came to King Dasaratha and asked for Rama's help."),
        Verse(kanda="Bala Kanda", kanda_num=1, sarga=2, verse_num=1,
              text="Rama, the mighty warrior, slew the demoness Tataka in the forest."),
        Verse(kanda="Ayodhya Kanda", kanda_num=2, sarga=1, verse_num=1,
              text="Kaikeyi demanded that Bharata be crowned king instead of Rama."),
        Verse(kanda="Sundara Kanda", kanda_num=5, sarga=1, verse_num=1,
              text="Hanuman leaped across the ocean to reach Lanka and find Sita."),
    ]


@pytest.fixture
def sample_entities():
    return [
        ExtractedEntity(name="Rama", entity_type=EntityType.CHARACTER, description="Prince of Ayodhya"),
        ExtractedEntity(name="Sita", entity_type=EntityType.CHARACTER, description="Wife of Rama"),
        ExtractedEntity(name="Lakshmana", entity_type=EntityType.CHARACTER, description="Brother of Rama"),
        ExtractedEntity(name="Hanuman", entity_type=EntityType.CHARACTER, description="Monkey god"),
        ExtractedEntity(name="Lanka", entity_type=EntityType.LOCATION, description="Demon kingdom"),
        ExtractedEntity(name="Ayodhya", entity_type=EntityType.LOCATION, description="Rama's city"),
    ]


@pytest.fixture
def sample_relationships():
    return [
        ExtractedRelationship(source="Rama", target="Sita", rel_type=RelationshipType.SPOUSE_OF),
        ExtractedRelationship(source="Dasaratha", target="Rama", rel_type=RelationshipType.FATHER_OF),
        ExtractedRelationship(source="Rama", target="Lakshmana", rel_type=RelationshipType.BROTHER_OF),
        ExtractedRelationship(source="Hanuman", target="Rama", rel_type=RelationshipType.SERVES),
        ExtractedRelationship(source="Ravana", target="Sita", rel_type=RelationshipType.KIDNAPS),
        ExtractedRelationship(source="Rama", target="Ravana", rel_type=RelationshipType.KILLS),
    ]
