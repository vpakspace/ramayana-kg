"""Pipeline orchestrator — download, parse, extract, build, embed."""

from __future__ import annotations

import logging
from pathlib import Path

from neo4j import Driver, GraphDatabase
from openai import OpenAI

from ramayana_kg.config import settings
from ramayana_kg.data.downloader import download_text
from ramayana_kg.data.parser import parse_file
from ramayana_kg.embeddings.vectorizer import (
    create_vector_indexes,
    embed_entities,
    embed_verses,
)
from ramayana_kg.extraction.alias_resolver import resolve_entities
from ramayana_kg.extraction.entity_extractor import extract_all_entities
from ramayana_kg.extraction.relationship_extractor import extract_all_relationships
from ramayana_kg.graph.builder import build_graph
from ramayana_kg.graph.schema import create_schema, get_stats
from ramayana_kg.models import Verse

logger = logging.getLogger(__name__)


def get_driver() -> Driver:
    return GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )


def get_client() -> OpenAI:
    return OpenAI(api_key=settings.openai_api_key)


def step_download(data_dir: str | None = None) -> Path:
    """Download Ramayana text."""
    path = download_text(output_dir=data_dir)
    logger.info("Downloaded to %s", path)
    return path


def step_parse(file_path: str | Path | None = None) -> list[Verse]:
    """Parse text into verses."""
    if file_path is None:
        file_path = Path(settings.data_dir) / "ramayana_griffith.txt"
    verses = parse_file(file_path)
    logger.info("Parsed %d verses", len(verses))
    return verses


def step_extract(verses: list[Verse], client: OpenAI | None = None) -> dict:
    """Extract entities and relationships from verses."""
    client = client or get_client()

    raw_entities = extract_all_entities(verses, client=client)
    entities = resolve_entities(raw_entities)

    relationships = extract_all_relationships(verses, client=client)

    logger.info(
        "Extraction complete: %d entities, %d relationships",
        len(entities), len(relationships),
    )
    return {"entities": entities, "relationships": relationships}


def step_build(
    driver: Driver, verses: list[Verse], extraction_result: dict
) -> dict:
    """Build the knowledge graph in Neo4j."""
    db = settings.neo4j_database
    create_schema(driver, database=db)
    result = build_graph(
        driver, verses,
        extraction_result["entities"],
        extraction_result["relationships"],
        database=db,
    )
    logger.info("Graph built: %s", result)
    return result


def step_embed(driver: Driver, verses: list[Verse], client: OpenAI | None = None) -> dict:
    """Embed verses and entities."""
    client = client or get_client()
    db = settings.neo4j_database

    create_vector_indexes(driver, database=db)
    verse_count = embed_verses(driver, verses, client=client, database=db)
    entity_count = embed_entities(driver, client=client, database=db)

    logger.info("Embedded %d verses, %d entities", verse_count, entity_count)
    return {"verses_embedded": verse_count, "entities_embedded": entity_count}


def run_full_pipeline(data_dir: str | None = None) -> dict:
    """Run the complete pipeline: download -> parse -> extract -> build -> embed."""
    driver = get_driver()
    client = get_client()

    try:
        # 1. Download
        file_path = step_download(data_dir)

        # 2. Parse
        verses = step_parse(file_path)

        # 3. Extract
        extraction = step_extract(verses, client=client)

        # 4. Build graph
        build_result = step_build(driver, verses, extraction)

        # 5. Embed
        embed_result = step_embed(driver, verses, client=client)

        stats = get_stats(driver, database=settings.neo4j_database)
        return {
            "verses_parsed": len(verses),
            **build_result,
            **embed_result,
            "stats": stats,
        }
    finally:
        driver.close()
