"""LLM-based entity extraction from Ramayana verses."""

from __future__ import annotations

import json
import logging
import time

from openai import APITimeoutError, OpenAI

from ramayana_kg.config import settings
from ramayana_kg.models import EntityType, ExtractedEntity, Verse

logger = logging.getLogger(__name__)

ENTITY_EXTRACTION_PROMPT = """You are an expert on the Indian epic Ramayana.
Extract all named entities from the following verses.

For each entity, provide:
- name: canonical English name
- type: one of Character, Location, Weapon, Event, Concept
- description: brief description (1 sentence)

Return a JSON array of objects. If no entities found, return [].

Verses:
{verses_text}

Return ONLY valid JSON array, no markdown fences."""


def extract_entities_batch(
    verses: list[Verse],
    client: OpenAI | None = None,
) -> list[ExtractedEntity]:
    """Extract entities from a batch of verses using LLM.

    Args:
        verses: batch of Verse objects (recommended: 20 per call)
        client: OpenAI client (created from settings if None)

    Returns:
        List of extracted entities with verse references.
    """
    if not verses:
        return []

    client = client or OpenAI(api_key=settings.openai_api_key)
    verses_text = "\n\n".join(
        f"[{v.verse_id}] {v.text}" for v in verses
    )

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You extract entities from ancient Indian texts.",
                    },
                    {
                        "role": "user",
                        "content": ENTITY_EXTRACTION_PROMPT.format(
                            verses_text=verses_text
                        ),
                    },
                ],
                temperature=0.1,
                max_tokens=2000,
                timeout=60,
            )
            raw = response.choices[0].message.content or "[]"
            return _parse_entities(raw, verses)
        except (APITimeoutError, Exception) as e:
            wait = 2 ** (attempt + 1)
            logger.warning(
                "API call failed (attempt %d/3): %s. Retrying in %ds...",
                attempt + 1, str(e)[:100], wait,
            )
            time.sleep(wait)

    logger.error("All retries exhausted for batch, skipping")
    return []


def _parse_entities(raw_json: str, verses: list[Verse]) -> list[ExtractedEntity]:
    """Parse LLM JSON response into ExtractedEntity objects."""
    raw_json = raw_json.strip()
    if raw_json.startswith("```"):
        raw_json = raw_json.split("\n", 1)[-1].rsplit("```", 1)[0]

    try:
        items = json.loads(raw_json)
    except json.JSONDecodeError:
        logger.warning("Failed to parse entity JSON: %s", raw_json[:200])
        return []

    if not isinstance(items, list):
        return []

    entities = []
    verse_ids = [v.verse_id for v in verses]
    default_verse_id = verse_ids[0] if verse_ids else ""

    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "").strip()
        if not name:
            continue

        entity_type_str = item.get("type", "Character")
        try:
            entity_type = EntityType(entity_type_str)
        except ValueError:
            entity_type = EntityType.CHARACTER

        entities.append(ExtractedEntity(
            name=name,
            entity_type=entity_type,
            description=item.get("description", ""),
            verse_id=item.get("verse_id", default_verse_id),
        ))

    return entities


def extract_all_entities(
    verses: list[Verse],
    batch_size: int | None = None,
    client: OpenAI | None = None,
) -> list[ExtractedEntity]:
    """Extract entities from all verses in batches.

    Args:
        verses: all verses
        batch_size: verses per LLM call (default from settings)
        client: OpenAI client

    Returns:
        All extracted entities (may contain duplicates).
    """
    batch_size = batch_size or settings.extraction_batch_size
    client = client or OpenAI(api_key=settings.openai_api_key)
    all_entities: list[ExtractedEntity] = []

    for i in range(0, len(verses), batch_size):
        batch = verses[i : i + batch_size]
        logger.info("Extracting entities from verses %d-%d", i, i + len(batch))
        entities = extract_entities_batch(batch, client=client)
        all_entities.extend(entities)

    logger.info("Total raw entities extracted: %d", len(all_entities))
    return all_entities
