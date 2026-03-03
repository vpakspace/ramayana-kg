"""Build the Ramayana Knowledge Graph in Neo4j."""

from __future__ import annotations

import logging

from neo4j import Driver

from ramayana_kg.models import (
    ExtractedEntity,
    ExtractedRelationship,
    Verse,
)

logger = logging.getLogger(__name__)


def build_structural_hierarchy(
    driver: Driver, verses: list[Verse], database: str = "ramayana"
) -> None:
    """Create Kanda -> Sarga -> Verse hierarchy."""
    with driver.session(database=database) as session:
        # Create Kandas
        kandas_seen: set[int] = set()
        for v in verses:
            if v.kanda_num not in kandas_seen:
                session.run(
                    "MERGE (k:Kanda {number: $num}) SET k.name = $name",
                    num=v.kanda_num, name=v.kanda,
                )
                kandas_seen.add(v.kanda_num)

        # Create Sargas and link to Kandas
        sargas_seen: set[str] = set()
        for v in verses:
            sarga_id = f"K{v.kanda_num}_S{v.sarga}"
            if sarga_id not in sargas_seen:
                session.run(
                    "MERGE (s:Sarga {sarga_id: $sid}) "
                    "SET s.number = $num, s.kanda_num = $kn "
                    "WITH s "
                    "MATCH (k:Kanda {number: $kn}) "
                    "MERGE (s)-[:BELONGS_TO]->(k)",
                    sid=sarga_id, num=v.sarga, kn=v.kanda_num,
                )
                sargas_seen.add(sarga_id)

        # Create Verses in batches
        batch_size = 200
        for i in range(0, len(verses), batch_size):
            batch = verses[i : i + batch_size]
            verse_data = [
                {
                    "vid": v.verse_id,
                    "text": v.text,
                    "kanda_num": v.kanda_num,
                    "sarga": v.sarga,
                    "verse_num": v.verse_num,
                    "sarga_id": f"K{v.kanda_num}_S{v.sarga}",
                }
                for v in batch
            ]
            session.run(
                "UNWIND $data AS v "
                "MERGE (verse:Verse {verse_id: v.vid}) "
                "SET verse.text = v.text, verse.kanda_num = v.kanda_num, "
                "    verse.sarga = v.sarga, verse.verse_num = v.verse_num "
                "WITH verse, v "
                "MATCH (s:Sarga {sarga_id: v.sarga_id}) "
                "MERGE (verse)-[:BELONGS_TO]->(s)",
                data=verse_data,
            )

    logger.info(
        "Structural hierarchy: %d kandas, %d sargas, %d verses",
        len(kandas_seen), len(sargas_seen), len(verses),
    )


def build_entity_nodes(
    driver: Driver,
    entities: list[ExtractedEntity],
    database: str = "ramayana",
) -> None:
    """Create entity nodes (Character, Location, Weapon, etc.)."""
    with driver.session(database=database) as session:
        for entity in entities:
            label = entity.entity_type.value
            session.run(
                f"MERGE (n:{label} {{name: $name}}) "
                "SET n.description = CASE WHEN n.description IS NULL "
                "  THEN $desc ELSE n.description + '; ' + $desc END",
                name=entity.name, desc=entity.description,
            )

            # Link entity to verse
            if entity.verse_id:
                session.run(
                    f"MATCH (n:{label} {{name: $name}}) "
                    "MATCH (v:Verse {verse_id: $vid}) "
                    "MERGE (n)-[:MENTIONED_IN]->(v)",
                    name=entity.name, vid=entity.verse_id,
                )

    logger.info("Created %d entity nodes", len(entities))


def build_relationships(
    driver: Driver,
    relationships: list[ExtractedRelationship],
    database: str = "ramayana",
) -> None:
    """Create relationships between entities."""
    with driver.session(database=database) as session:
        for rel in relationships:
            # Use dynamic relationship type via APOC-free approach
            query = (
                "MATCH (s {name: $source}), (t {name: $target}) "
                f"MERGE (s)-[r:{rel.rel_type.value}]->(t) "
                "SET r.description = $desc, r.verse_id = $vid"
            )
            session.run(
                query,
                source=rel.source,
                target=rel.target,
                desc=rel.description,
                vid=rel.verse_id,
            )

    logger.info("Created %d relationships", len(relationships))


def build_graph(
    driver: Driver,
    verses: list[Verse],
    entities: list[ExtractedEntity],
    relationships: list[ExtractedRelationship],
    database: str = "ramayana",
) -> dict:
    """Build the complete knowledge graph."""
    build_structural_hierarchy(driver, verses, database)
    build_entity_nodes(driver, entities, database)
    build_relationships(driver, relationships, database)
    return {"verses": len(verses), "entities": len(entities), "relationships": len(relationships)}
