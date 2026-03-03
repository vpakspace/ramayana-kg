"""Domain models for Ramayana Knowledge Graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EntityType(StrEnum):
    CHARACTER = "Character"
    LOCATION = "Location"
    WEAPON = "Weapon"
    EVENT = "Event"
    CONCEPT = "Concept"


class RelationshipType(StrEnum):
    FATHER_OF = "FATHER_OF"
    MOTHER_OF = "MOTHER_OF"
    SPOUSE_OF = "SPOUSE_OF"
    BROTHER_OF = "BROTHER_OF"
    SISTER_OF = "SISTER_OF"
    SON_OF = "SON_OF"
    FIGHTS = "FIGHTS"
    ALLIES_WITH = "ALLIES_WITH"
    RULES = "RULES"
    TRAVELS_TO = "TRAVELS_TO"
    WIELDS = "WIELDS"
    KILLS = "KILLS"
    KIDNAPS = "KIDNAPS"
    RESCUES = "RESCUES"
    MENTIONED_IN = "MENTIONED_IN"
    BELONGS_TO = "BELONGS_TO"
    SERVES = "SERVES"
    TEACHES = "TEACHES"


@dataclass
class Verse:
    kanda: str  # Book name (e.g. "Bala Kanda")
    kanda_num: int  # 1-6
    sarga: int  # Canto number
    verse_num: int  # Verse number within sarga
    text: str
    verse_id: str = ""

    def __post_init__(self):
        if not self.verse_id:
            self.verse_id = f"K{self.kanda_num}_S{self.sarga}_V{self.verse_num}"


@dataclass
class Character:
    name: str
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    entity_type: EntityType = EntityType.CHARACTER


@dataclass
class ExtractedEntity:
    name: str
    entity_type: EntityType
    description: str = ""
    verse_id: str = ""
    confidence: float = 1.0


@dataclass
class ExtractedRelationship:
    source: str
    target: str
    rel_type: RelationshipType
    description: str = ""
    verse_id: str = ""
    confidence: float = 1.0


@dataclass
class GraphContext:
    entities: list[dict] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    source_verses: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    verse_id: str
    text: str
    score: float
    kanda: str = ""
    sarga: int = 0


@dataclass
class QAResult:
    answer: str
    sources: list[SearchResult] = field(default_factory=list)
    graph_context: GraphContext | None = None
    mode: str = "hybrid"
    confidence: float = 0.0
