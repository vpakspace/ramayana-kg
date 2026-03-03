"""Hybrid retriever: vector entry + graph traversal."""

from __future__ import annotations

import logging

from neo4j import Driver
from openai import OpenAI

from ramayana_kg.config import settings
from ramayana_kg.embeddings.vectorizer import vector_search
from ramayana_kg.graph.queries import (
    character_profile,
    get_entity_relationships,
    get_entity_verses,
    search_entities,
)
from ramayana_kg.models import GraphContext, SearchResult

logger = logging.getLogger(__name__)


def retrieve_vector(
    driver: Driver,
    query: str,
    top_k: int | None = None,
    client: OpenAI | None = None,
    database: str = "ramayana",
) -> list[SearchResult]:
    """Pure vector similarity search."""
    results = vector_search(driver, query, top_k=top_k, client=client, database=database)
    return [
        SearchResult(
            verse_id=r["verse_id"],
            text=r["text"],
            score=r["score"],
            kanda=str(r.get("kanda_num", "")),
            sarga=r.get("sarga", 0),
        )
        for r in results
    ]


def retrieve_graph(
    driver: Driver,
    query: str,
    depth: int | None = None,
    database: str = "ramayana",
) -> GraphContext:
    """Pure graph traversal based on entity search."""
    depth = depth or settings.graph_depth

    # Find entities matching the query
    entities = search_entities(driver, query, limit=5, database=database)
    if not entities:
        return GraphContext()

    context = GraphContext()
    for entity in entities:
        context.entities.append({
            "name": entity["name"],
            "label": entity["label"],
            "description": entity.get("description", ""),
        })

        # Get relationships
        rels = get_entity_relationships(driver, entity["name"], database=database)
        for rel in rels:
            context.relationships.append(rel)

        # Get source verses
        verses = get_entity_verses(driver, entity["name"], limit=5, database=database)
        for v in verses:
            context.source_verses.append(v["text"])

    return context


def retrieve_hybrid(
    driver: Driver,
    query: str,
    top_k: int | None = None,
    client: OpenAI | None = None,
    database: str = "ramayana",
) -> tuple[list[SearchResult], GraphContext]:
    """Hybrid retrieval: vector entry -> graph expansion.

    1. Vector search to find relevant verses
    2. Extract entity mentions from top results
    3. Graph traversal from those entities
    4. Combine passages from both sources

    Returns (search_results, graph_context).
    """
    top_k = top_k or settings.top_k_vector
    client = client or OpenAI(api_key=settings.openai_api_key)

    # Step 1: Vector search
    vector_results = retrieve_vector(driver, query, top_k=top_k, client=client, database=database)

    # Step 2: Graph context from query entities
    graph_context = retrieve_graph(driver, query, database=database)

    # Step 3: If we found entities in graph, get their profiles
    for entity in graph_context.entities[:3]:
        name = entity.get("name", "")
        if name and entity.get("label") == "Character":
            profile = character_profile(driver, name, database=database)
            if profile:
                for rel in profile.get("outgoing", []):
                    path = f"{name} -[{rel['type']}]-> {rel['target']}"
                    if path not in graph_context.paths:
                        graph_context.paths.append(path)
                for rel in profile.get("incoming", []):
                    path = f"{rel['source']} -[{rel['type']}]-> {name}"
                    if path not in graph_context.paths:
                        graph_context.paths.append(path)

    # Rerank: boost vector results that mention graph entities
    entity_names = {e["name"].lower() for e in graph_context.entities}
    for result in vector_results:
        text_lower = result.text.lower()
        boost = sum(0.05 for name in entity_names if name in text_lower)
        result.score = min(result.score + boost, 1.0)

    vector_results.sort(key=lambda r: r.score, reverse=True)

    return vector_results[:settings.top_k_final], graph_context
