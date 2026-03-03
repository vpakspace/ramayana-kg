"""Multi-hop Cypher query library for Ramayana KG."""

from __future__ import annotations

import logging

from neo4j import Driver

logger = logging.getLogger(__name__)


def character_profile(driver: Driver, name: str, database: str = "ramayana") -> dict:
    """Get complete character profile with relationships."""
    with driver.session(database=database) as session:
        result = session.run(
            "MATCH (c:Character {name: $name}) "
            "OPTIONAL MATCH (c)-[r]->(t) "
            "RETURN c.name AS name, c.description AS description, "
            "  collect({type: type(r), target: t.name}) AS outgoing",
            name=name,
        )
        record = result.single()
        if not record:
            return {}

        # Incoming relationships
        incoming_result = session.run(
            "MATCH (s)-[r]->(c:Character {name: $name}) "
            "RETURN collect({type: type(r), source: s.name}) AS incoming",
            name=name,
        )
        incoming_record = incoming_result.single()

        return {
            "name": record["name"],
            "description": record["description"],
            "outgoing": [r for r in record["outgoing"] if r["type"]],
            "incoming": [r for r in (incoming_record["incoming"] if incoming_record else []) if r["type"]],
        }


def family_tree(driver: Driver, name: str, database: str = "ramayana") -> list[dict]:
    """Get family tree for a character (parents, siblings, spouse, children)."""
    with driver.session(database=database) as session:
        result = session.run(
            "MATCH (c:Character {name: $name}) "
            "OPTIONAL MATCH (c)-[r:FATHER_OF|MOTHER_OF|SPOUSE_OF|BROTHER_OF|SISTER_OF|SON_OF]->(t) "
            "WITH c, collect({rel: type(r), name: t.name}) AS family_out "
            "OPTIONAL MATCH (s)-[r2:FATHER_OF|MOTHER_OF|SPOUSE_OF|BROTHER_OF|SISTER_OF|SON_OF]->(c) "
            "RETURN c.name AS name, family_out, "
            "  collect({rel: type(r2), name: s.name}) AS family_in",
            name=name,
        )
        record = result.single()
        if not record:
            return []

        family = []
        for r in record["family_out"]:
            if r["rel"]:
                family.append({"relation": r["rel"], "name": r["name"], "direction": "outgoing"})
        for r in record["family_in"]:
            if r["rel"]:
                family.append({"relation": r["rel"], "name": r["name"], "direction": "incoming"})
        return family


def shortest_path(
    driver: Driver, source: str, target: str, database: str = "ramayana"
) -> list[str]:
    """Find shortest path between two entities."""
    with driver.session(database=database) as session:
        result = session.run(
            "MATCH p = shortestPath((a {name: $source})-[*..6]-(b {name: $target})) "
            "RETURN [n IN nodes(p) | n.name] AS path_names, "
            "  [r IN relationships(p) | type(r)] AS rel_types",
            source=source, target=target,
        )
        record = result.single()
        if not record:
            return []

        path_names = record["path_names"]
        rel_types = record["rel_types"]
        path_desc = []
        for i, rel in enumerate(rel_types):
            path_desc.append(f"{path_names[i]} -[{rel}]-> {path_names[i+1]}")
        return path_desc


def co_occurrence(
    driver: Driver, top_n: int = 20, kanda_num: int | None = None, database: str = "ramayana"
) -> list[dict]:
    """Find top co-occurring character pairs (mentioned in same sarga)."""
    kanda_filter = "AND v.kanda_num = $kanda_num" if kanda_num else ""
    with driver.session(database=database) as session:
        result = session.run(
            "MATCH (c1:Character)-[:MENTIONED_IN]->(v:Verse)<-[:MENTIONED_IN]-(c2:Character) "
            f"WHERE id(c1) < id(c2) {kanda_filter} "
            "RETURN c1.name AS char1, c2.name AS char2, count(v) AS co_count "
            "ORDER BY co_count DESC LIMIT $limit",
            limit=top_n,
            kanda_num=kanda_num,
        )
        return [{"char1": r["char1"], "char2": r["char2"], "count": r["co_count"]} for r in result]


def search_entities(driver: Driver, query: str, limit: int = 10, database: str = "ramayana") -> list[dict]:
    """Fulltext search across all entity types."""
    with driver.session(database=database) as session:
        result = session.run(
            "CALL db.index.fulltext.queryNodes('entity_fulltext', $query) "
            "YIELD node, score "
            "RETURN node.name AS name, labels(node)[0] AS label, "
            "  node.description AS description, score "
            "ORDER BY score DESC LIMIT $limit",
            query=query, limit=limit,
        )
        return [dict(r) for r in result]


def get_entity_verses(
    driver: Driver, name: str, limit: int = 10, database: str = "ramayana"
) -> list[dict]:
    """Get verses mentioning a specific entity."""
    with driver.session(database=database) as session:
        result = session.run(
            "MATCH (n {name: $name})-[:MENTIONED_IN]->(v:Verse) "
            "RETURN v.verse_id AS verse_id, v.text AS text, "
            "  v.kanda_num AS kanda_num, v.sarga AS sarga "
            "ORDER BY v.verse_id LIMIT $limit",
            name=name, limit=limit,
        )
        return [dict(r) for r in result]


def get_entity_relationships(
    driver: Driver, name: str, database: str = "ramayana"
) -> list[dict]:
    """Get all relationships for an entity."""
    with driver.session(database=database) as session:
        outgoing = session.run(
            "MATCH (n {name: $name})-[r]->(t) "
            "WHERE NOT type(r) = 'MENTIONED_IN' AND NOT type(r) = 'BELONGS_TO' "
            "RETURN type(r) AS rel_type, t.name AS target, r.description AS description",
            name=name,
        )
        incoming = session.run(
            "MATCH (s)-[r]->(n {name: $name}) "
            "WHERE NOT type(r) = 'MENTIONED_IN' AND NOT type(r) = 'BELONGS_TO' "
            "RETURN type(r) AS rel_type, s.name AS source, r.description AS description",
            name=name,
        )
        results = []
        for r in outgoing:
            results.append({"type": r["rel_type"], "direction": "->", "other": r["target"], "description": r["description"]})
        for r in incoming:
            results.append({"type": r["rel_type"], "direction": "<-", "other": r["source"], "description": r["description"]})
        return results
