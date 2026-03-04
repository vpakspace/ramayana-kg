"""Neo4j schema: constraints, indexes, and initialization."""

from __future__ import annotations

import logging

from neo4j import Driver

logger = logging.getLogger(__name__)

CONSTRAINTS = [
    "CREATE CONSTRAINT character_name IF NOT EXISTS FOR (c:Character) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT location_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
    "CREATE CONSTRAINT weapon_name IF NOT EXISTS FOR (w:Weapon) REQUIRE w.name IS UNIQUE",
    "CREATE CONSTRAINT event_name IF NOT EXISTS FOR (e:Event) REQUIRE e.name IS UNIQUE",
    "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT verse_id IF NOT EXISTS FOR (v:Verse) REQUIRE v.verse_id IS UNIQUE",
    "CREATE CONSTRAINT kanda_num IF NOT EXISTS FOR (k:Kanda) REQUIRE k.number IS UNIQUE",
    "CREATE CONSTRAINT sarga_id IF NOT EXISTS FOR (s:Sarga) REQUIRE s.sarga_id IS UNIQUE",
]

FULLTEXT_INDEXES = [
    (
        "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS "
        "FOR (n:Character|Location|Weapon|Event|Concept) ON EACH [n.name, n.description]"
    ),
    (
        "CREATE FULLTEXT INDEX verse_fulltext IF NOT EXISTS "
        "FOR (v:Verse) ON EACH [v.text]"
    ),
]


def create_schema(driver: Driver, database: str = "ramayana") -> None:
    """Create all constraints and indexes in Neo4j."""
    with driver.session(database=database) as session:
        for stmt in CONSTRAINTS:
            try:
                session.run(stmt)
            except Exception as e:
                logger.debug("Constraint may already exist: %s", e)

        for stmt in FULLTEXT_INDEXES:
            try:
                session.run(stmt)
            except Exception as e:
                logger.debug("Index may already exist: %s", e)

    logger.info(
        "Schema created: %d constraints, %d indexes",
        len(CONSTRAINTS), len(FULLTEXT_INDEXES),
    )


def clear_database(driver: Driver, database: str = "ramayana") -> int:
    """Delete all nodes and relationships. Returns count of deleted nodes."""
    with driver.session(database=database) as session:
        result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) AS cnt")
        record = result.single()
        count = record["cnt"] if record else 0
    logger.info("Cleared database: %d nodes deleted", count)
    return count


def get_stats(driver: Driver, database: str = "ramayana") -> dict:
    """Get node and relationship counts."""
    with driver.session(database=database) as session:
        nodes = session.run("MATCH (n) RETURN count(n) AS cnt").single()
        rels = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()

        # Count by label
        labels_result = session.run(
            "MATCH (n) UNWIND labels(n) AS label "
            "RETURN label, count(*) AS cnt ORDER BY cnt DESC"
        )
        label_counts = {r["label"]: r["cnt"] for r in labels_result}

        # Count by relationship type
        rel_types_result = session.run(
            "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(*) AS cnt "
            "ORDER BY cnt DESC"
        )
        rel_type_counts = {r["rel_type"]: r["cnt"] for r in rel_types_result}

    return {
        "total_nodes": nodes["cnt"] if nodes else 0,
        "total_relationships": rels["cnt"] if rels else 0,
        "nodes_by_label": label_counts,
        "relationships_by_type": rel_type_counts,
    }
