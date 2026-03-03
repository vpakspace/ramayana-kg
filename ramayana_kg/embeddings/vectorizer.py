"""Vector embeddings for verses and entities using OpenAI + Neo4j Vector Index."""

from __future__ import annotations

import logging

from neo4j import Driver
from openai import OpenAI

from ramayana_kg.config import settings
from ramayana_kg.models import Verse

logger = logging.getLogger(__name__)

VECTOR_INDEX_VERSE = "verse_vector_index"
VECTOR_INDEX_ENTITY = "entity_vector_index"


def create_vector_indexes(driver: Driver, database: str = "ramayana") -> None:
    """Create Neo4j vector indexes for similarity search."""
    dim = settings.embedding_dimensions
    with driver.session(database=database) as session:
        try:
            session.run(
                "CREATE VECTOR INDEX $name IF NOT EXISTS "
                "FOR (v:Verse) ON (v.embedding) "
                "OPTIONS {indexConfig: {"
                "  `vector.dimensions`: $dim, "
                "  `vector.similarity_function`: 'cosine'"
                "}}",
                name=VECTOR_INDEX_VERSE, dim=dim,
            )
        except Exception as e:
            logger.debug("Verse vector index may exist: %s", e)

        try:
            session.run(
                "CREATE VECTOR INDEX $name IF NOT EXISTS "
                "FOR (n:Character) ON (n.embedding) "
                "OPTIONS {indexConfig: {"
                "  `vector.dimensions`: $dim, "
                "  `vector.similarity_function`: 'cosine'"
                "}}",
                name=VECTOR_INDEX_ENTITY, dim=dim,
            )
        except Exception as e:
            logger.debug("Entity vector index may exist: %s", e)

    logger.info("Vector indexes created (dim=%d)", dim)


def embed_texts(texts: list[str], client: OpenAI | None = None) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    if not texts:
        return []
    client = client or OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
        dimensions=settings.embedding_dimensions,
    )
    return [item.embedding for item in response.data]


def embed_verses(
    driver: Driver,
    verses: list[Verse],
    client: OpenAI | None = None,
    batch_size: int = 100,
    database: str = "ramayana",
) -> int:
    """Embed all verses and store embeddings in Neo4j.

    Returns count of embedded verses.
    """
    client = client or OpenAI(api_key=settings.openai_api_key)
    total = 0

    for i in range(0, len(verses), batch_size):
        batch = verses[i : i + batch_size]
        texts = [v.text for v in batch]
        embeddings = embed_texts(texts, client=client)

        with driver.session(database=database) as session:
            for verse, embedding in zip(batch, embeddings):
                session.run(
                    "MATCH (v:Verse {verse_id: $vid}) SET v.embedding = $emb",
                    vid=verse.verse_id, emb=embedding,
                )

        total += len(batch)
        logger.info("Embedded %d / %d verses", total, len(verses))

    return total


def embed_entities(
    driver: Driver,
    client: OpenAI | None = None,
    database: str = "ramayana",
) -> int:
    """Embed entity descriptions and store in Neo4j.

    Returns count of embedded entities.
    """
    client = client or OpenAI(api_key=settings.openai_api_key)

    with driver.session(database=database) as session:
        result = session.run(
            "MATCH (n) WHERE n:Character OR n:Location OR n:Weapon OR n:Event OR n:Concept "
            "RETURN n.name AS name, n.description AS description, labels(n)[0] AS label"
        )
        entities = [dict(r) for r in result]

    if not entities:
        return 0

    texts = [f"{e['name']}: {e['description'] or e['name']}" for e in entities]
    embeddings = embed_texts(texts, client=client)

    with driver.session(database=database) as session:
        for entity, embedding in zip(entities, embeddings):
            label = entity["label"]
            session.run(
                f"MATCH (n:{label} {{name: $name}}) SET n.embedding = $emb",
                name=entity["name"], emb=embedding,
            )

    logger.info("Embedded %d entities", len(entities))
    return len(entities)


def vector_search(
    driver: Driver,
    query: str,
    top_k: int | None = None,
    client: OpenAI | None = None,
    database: str = "ramayana",
) -> list[dict]:
    """Search verses by vector similarity.

    Returns list of {verse_id, text, score, kanda_num, sarga}.
    """
    top_k = top_k or settings.top_k_vector
    client = client or OpenAI(api_key=settings.openai_api_key)

    query_embedding = embed_texts([query], client=client)[0]

    with driver.session(database=database) as session:
        result = session.run(
            "CALL db.index.vector.queryNodes($index, $k, $embedding) "
            "YIELD node, score "
            "RETURN node.verse_id AS verse_id, node.text AS text, score, "
            "  node.kanda_num AS kanda_num, node.sarga AS sarga "
            "ORDER BY score DESC",
            index=VECTOR_INDEX_VERSE, k=top_k, embedding=query_embedding,
        )
        return [dict(r) for r in result]
