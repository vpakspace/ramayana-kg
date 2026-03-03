"""LLM answer generation with structured context from Ramayana KG."""

from __future__ import annotations

import logging

from neo4j import Driver
from openai import OpenAI

from ramayana_kg.config import settings
from ramayana_kg.models import GraphContext, QAResult, SearchResult
from ramayana_kg.rag.retriever import retrieve_graph, retrieve_hybrid, retrieve_vector

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert scholar of the Ramayana, the ancient Indian epic.
Answer questions based on the provided context from Griffith's translation.
Be accurate, cite verse references when possible, and provide insightful analysis.
If the context doesn't contain enough information, say so honestly."""

CONTEXT_TEMPLATE = """## Verse Passages
{verse_passages}

## Knowledge Graph Context
{graph_context}

## Question
{question}

Provide a comprehensive answer based on the above context. Reference specific verses when possible."""


def format_verse_passages(results: list[SearchResult]) -> str:
    """Format search results as passage text."""
    if not results:
        return "No relevant verses found."
    lines = []
    for r in results:
        lines.append(f"[{r.verse_id}] (score: {r.score:.3f})\n{r.text}")
    return "\n\n".join(lines)


def format_graph_context(ctx: GraphContext) -> str:
    """Format graph context as readable text."""
    parts = []
    if ctx.entities:
        entities_text = ", ".join(
            f"{e['name']} ({e.get('label', 'Entity')})" for e in ctx.entities
        )
        parts.append(f"Entities: {entities_text}")

    if ctx.paths:
        parts.append("Relationships:\n" + "\n".join(f"  - {p}" for p in ctx.paths[:15]))

    if ctx.relationships:
        rels = []
        for r in ctx.relationships[:10]:
            other = r.get("other", "?")
            rels.append(f"  - {r['type']} {r['direction']} {other}")
        if rels:
            parts.append("Direct relationships:\n" + "\n".join(rels))

    return "\n".join(parts) if parts else "No graph context available."


def generate_answer(
    question: str,
    driver: Driver,
    mode: str = "hybrid",
    client: OpenAI | None = None,
    database: str = "ramayana",
) -> QAResult:
    """Generate an answer using the specified retrieval mode.

    Args:
        question: user's question
        driver: Neo4j driver
        mode: "vector", "graph", or "hybrid"
        client: OpenAI client
        database: Neo4j database name

    Returns:
        QAResult with answer, sources, and graph context.
    """
    client = client or OpenAI(api_key=settings.openai_api_key)
    search_results: list[SearchResult] = []
    graph_context = GraphContext()

    if mode == "vector":
        search_results = retrieve_vector(driver, question, client=client, database=database)
        search_results = search_results[:settings.top_k_final]
    elif mode == "graph":
        graph_context = retrieve_graph(driver, question, database=database)
    else:  # hybrid
        search_results, graph_context = retrieve_hybrid(
            driver, question, client=client, database=database
        )

    # Build context for LLM
    verses_text = format_verse_passages(search_results)
    graph_text = format_graph_context(graph_context)

    user_message = CONTEXT_TEMPLATE.format(
        verse_passages=verses_text,
        graph_context=graph_text,
        question=question,
    )

    # Truncate if too long
    if len(user_message) > settings.max_context_tokens * 4:
        user_message = user_message[:settings.max_context_tokens * 4]

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=settings.temperature,
        max_tokens=1500,
    )

    answer = response.choices[0].message.content or ""

    # Estimate confidence from search scores
    confidence = 0.0
    if search_results:
        confidence = sum(r.score for r in search_results) / len(search_results)
    elif graph_context.entities:
        confidence = 0.5  # Graph-only has moderate confidence

    return QAResult(
        answer=answer,
        sources=search_results,
        graph_context=graph_context,
        mode=mode,
        confidence=min(confidence, 1.0),
    )
