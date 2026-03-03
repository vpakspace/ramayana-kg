"""LLM-based relationship extraction from Ramayana verses."""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from ramayana_kg.config import settings
from ramayana_kg.models import ExtractedRelationship, RelationshipType, Verse

logger = logging.getLogger(__name__)

VALID_REL_TYPES = {rt.value for rt in RelationshipType}

RELATIONSHIP_EXTRACTION_PROMPT = """You are an expert on the Indian epic Ramayana.
Extract relationships between named entities from the following verses.

Valid relationship types:
FATHER_OF, MOTHER_OF, SPOUSE_OF, BROTHER_OF, SISTER_OF, SON_OF,
FIGHTS, ALLIES_WITH, RULES, TRAVELS_TO, WIELDS, KILLS, KIDNAPS,
RESCUES, SERVES, TEACHES

For each relationship, provide:
- source: entity name performing the action
- target: entity name receiving the action
- rel_type: one of the types above
- description: brief context (1 sentence)

Return a JSON array. If no relationships found, return [].

Verses:
{verses_text}

Return ONLY valid JSON array, no markdown fences."""


def extract_relationships_batch(
    verses: list[Verse],
    client: OpenAI | None = None,
) -> list[ExtractedRelationship]:
    """Extract relationships from a batch of verses using LLM."""
    if not verses:
        return []

    client = client or OpenAI(api_key=settings.openai_api_key)
    verses_text = "\n\n".join(
        f"[{v.verse_id}] {v.text}" for v in verses
    )

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": "You extract relationships from ancient Indian texts."},
            {"role": "user", "content": RELATIONSHIP_EXTRACTION_PROMPT.format(verses_text=verses_text)},
        ],
        temperature=0.1,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content or "[]"
    return _parse_relationships(raw, verses)


def _parse_relationships(raw_json: str, verses: list[Verse]) -> list[ExtractedRelationship]:
    """Parse LLM JSON response into ExtractedRelationship objects."""
    raw_json = raw_json.strip()
    if raw_json.startswith("```"):
        raw_json = raw_json.split("\n", 1)[-1].rsplit("```", 1)[0]

    try:
        items = json.loads(raw_json)
    except json.JSONDecodeError:
        logger.warning("Failed to parse relationship JSON: %s", raw_json[:200])
        return []

    if not isinstance(items, list):
        return []

    relationships = []
    verse_ids = [v.verse_id for v in verses]
    default_verse_id = verse_ids[0] if verse_ids else ""

    for item in items:
        if not isinstance(item, dict):
            continue
        source = item.get("source", "").strip()
        target = item.get("target", "").strip()
        rel_type_str = item.get("rel_type", "").strip()

        if not source or not target or not rel_type_str:
            continue
        if rel_type_str not in VALID_REL_TYPES:
            continue

        relationships.append(ExtractedRelationship(
            source=source,
            target=target,
            rel_type=RelationshipType(rel_type_str),
            description=item.get("description", ""),
            verse_id=item.get("verse_id", default_verse_id),
        ))

    return relationships


def extract_all_relationships(
    verses: list[Verse],
    batch_size: int | None = None,
    client: OpenAI | None = None,
) -> list[ExtractedRelationship]:
    """Extract relationships from all verses in batches."""
    batch_size = batch_size or settings.extraction_batch_size
    client = client or OpenAI(api_key=settings.openai_api_key)
    all_rels: list[ExtractedRelationship] = []

    for i in range(0, len(verses), batch_size):
        batch = verses[i : i + batch_size]
        logger.info("Extracting relationships from verses %d-%d", i, i + len(batch))
        rels = extract_relationships_batch(batch, client=client)
        all_rels.extend(rels)

    logger.info("Total raw relationships extracted: %d", len(all_rels))
    return all_rels
