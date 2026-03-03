"""Resolve entity aliases and merge duplicates."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from thefuzz import fuzz

from ramayana_kg.config import settings
from ramayana_kg.models import ExtractedEntity

logger = logging.getLogger(__name__)


def load_seed_characters(seed_path: str | Path | None = None) -> dict[str, list[str]]:
    """Load character seed data as {canonical_name: [aliases]}.

    Returns mapping including reverse lookups (alias -> canonical).
    """
    if seed_path is None:
        seed_path = Path(__file__).parent.parent / "data" / "characters_seed.json"
    else:
        seed_path = Path(seed_path)

    if not seed_path.exists():
        return {}

    with open(seed_path, encoding="utf-8") as f:
        items = json.load(f)

    seed_map: dict[str, list[str]] = {}
    for item in items:
        name = item["name"]
        aliases = item.get("aliases", [])
        seed_map[name] = aliases
    return seed_map


def build_alias_index(seed_map: dict[str, list[str]]) -> dict[str, str]:
    """Build reverse index: lowercase alias/name -> canonical name."""
    index: dict[str, str] = {}
    for canonical, aliases in seed_map.items():
        index[canonical.lower()] = canonical
        for alias in aliases:
            index[alias.lower()] = canonical
    return index


def resolve_name(
    name: str,
    alias_index: dict[str, str],
    threshold: float | None = None,
) -> str:
    """Resolve a name to its canonical form.

    1. Exact match in alias index
    2. Fuzzy match above threshold
    3. Return original name (title-cased)
    """
    threshold = threshold or settings.alias_fuzzy_threshold

    # Exact match
    lower_name = name.lower().strip()
    if lower_name in alias_index:
        return alias_index[lower_name]

    # Fuzzy match against all known names/aliases
    best_score = 0
    best_match = ""
    for key, canonical in alias_index.items():
        score = fuzz.ratio(lower_name, key) / 100.0
        if score > best_score:
            best_score = score
            best_match = canonical

    if best_score >= threshold:
        return best_match

    # No match — title-case the original
    return name.strip().title()


def resolve_entities(
    entities: list[ExtractedEntity],
    seed_path: str | Path | None = None,
) -> list[ExtractedEntity]:
    """Resolve all entity names to canonical forms and deduplicate.

    Returns deduplicated list with merged descriptions.
    """
    seed_map = load_seed_characters(seed_path)
    alias_index = build_alias_index(seed_map)

    # Resolve names
    for entity in entities:
        entity.name = resolve_name(entity.name, alias_index)

    # Deduplicate by (name, entity_type)
    seen: dict[tuple[str, str], ExtractedEntity] = {}
    for entity in entities:
        key = (entity.name, entity.entity_type.value)
        if key not in seen:
            seen[key] = entity
        else:
            existing = seen[key]
            if entity.description and entity.description not in existing.description:
                if existing.description:
                    existing.description += "; " + entity.description
                else:
                    existing.description = entity.description

    result = list(seen.values())
    logger.info("Resolved %d entities to %d unique", len(entities), len(result))
    return result
