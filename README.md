# Ramayana Knowledge Graph

LLM-powered entity extraction and hybrid RAG system built on Griffith's English translation of the Indian epic Ramayana.

Automatically extracts characters, locations, weapons, events and relationships from 3700+ verses using GPT-4o-mini, stores them in a Neo4j knowledge graph with vector indexes, and provides hybrid retrieval-augmented generation for Q&A in English and Russian.

## Architecture

```
┌─────────────┐     ┌─────────┐     ┌───────────────┐     ┌──────────┐     ┌─────────────┐
│  Gutenberg   │────▶│  Parser  │────▶│ LLM Extraction│────▶│  Neo4j   │────▶│ Hybrid RAG  │
│  Text (2.4MB)│     │3719 verse│     │ gpt-4o-mini   │     │  Graph   │     │ + Streamlit │
└─────────────┘     └─────────┘     └───────────────┘     └──────────┘     └─────────────┘
                     6 Kandas         2979 entities          5162 nodes       Vector+Graph
                     493 Sargas       762 relationships      5332 edges       EN/RU Q&A
```

## Knowledge Graph Stats

| Node Type   | Count | Description                        |
|-------------|------:|-------------------------------------|
| Verse       | 3,719 | Parsed stanzas from Griffith's text |
| Sarga       |   493 | Cantos (chapters)                   |
| Character   |   490 | Rama, Sita, Hanuman, Ravana...      |
| Location    |   238 | Ayodhya, Lanka, Dandaka Forest...   |
| Concept     |   165 | Dharma, Tapas, Sacrifice...         |
| Event       |    35 | Coronation, Exile, Battle...        |
| Weapon      |    16 | Brahmastra, Gandiva...              |
| Kanda       |     6 | Books of the Ramayana               |
| **Total**   | **5,162** |                                 |

**Relationships:** 5,332 edges — FATHER_OF, SPOUSE_OF, KILLS, FIGHTS, ALLIES_WITH, RESCUES, TEACHES, SERVES, RULES, KIDNAPS, BROTHER_OF, MOTHER_OF, SON_OF, SISTER_OF, TRAVELS_TO, MENTIONED_IN, BELONGS_TO

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for Neo4j)
- OpenAI API key

### Installation

```bash
git clone https://github.com/vpakspace/ramayana-kg.git
cd ramayana-kg
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set OPENAI_API_KEY
```

### Start Neo4j

```bash
docker run -d --name ramayana-neo4j \
  -p 7475:7474 -p 7688:7687 \
  -e NEO4J_AUTH=neo4j/ramayana2026 \
  neo4j:5-community
```

### Run Pipeline

```bash
# Full pipeline: download → parse → extract → build graph → embed
python run_pipeline.py all

# Or step by step:
python run_pipeline.py download    # Download from Project Gutenberg
python run_pipeline.py parse       # Parse into 3719 verses
python run_pipeline.py extract     # LLM entity + relationship extraction
python run_pipeline.py build       # Build Neo4j knowledge graph
python run_pipeline.py embed       # Generate vector embeddings
```

Full pipeline takes ~60-70 minutes (mostly LLM extraction).

### Query

```bash
# English
python run_pipeline.py query "Who is Rama?"

# Russian
python run_pipeline.py query "Кто такой Рама?" --lang ru

# Different modes
python run_pipeline.py query "Who killed Ravana?" --mode vector
python run_pipeline.py query "What is the family of Dasaratha?" --mode graph
python run_pipeline.py query "Describe the battle of Lanka" --mode hybrid
```

### Streamlit UI

```bash
./run_streamlit.sh
# Open http://localhost:8507
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `all` | Run full pipeline (download → embed) |
| `download` | Download Griffith's Ramayana from Gutenberg |
| `parse` | Parse text into structured verses |
| `extract` | Extract entities and relationships via LLM |
| `build` | Build Neo4j knowledge graph |
| `embed` | Generate OpenAI embeddings for verses and entities |
| `query "<question>"` | Ask a question (options: `--mode`, `--lang`) |
| `stats` | Show graph statistics as JSON |
| `clear -y` | Clear all data from Neo4j |

## Streamlit UI

5 interactive tabs with English/Russian language switcher:

1. **KG Explorer** — search entities, view relationships, family trees, shortest paths between characters
2. **Hybrid Search & Q&A** — ask questions in 3 retrieval modes (vector, graph, hybrid) with source citations
3. **Dashboard** — node/edge distribution charts, kanda breakdown
4. **Co-occurrence** — character pair analysis with kanda filter
5. **Settings** — configuration display, graph stats, clear database

## Project Structure

```
ramayana-kg/
├── run_pipeline.py              # CLI entry point
├── streamlit_app.py             # Streamlit UI
├── requirements.txt
├── pyproject.toml
├── ramayana_kg/
│   ├── config.py                # Pydantic Settings (.env)
│   ├── models.py                # Verse, Entity, Relationship, QAResult
│   ├── pipeline.py              # 5-step pipeline orchestrator
│   ├── data/
│   │   ├── downloader.py        # Project Gutenberg downloader
│   │   └── parser.py            # Griffith text → Verse objects
│   ├── extraction/
│   │   ├── entity_extractor.py  # LLM entity extraction + retry
│   │   ├── relationship_extractor.py  # LLM relationship extraction + retry
│   │   └── alias_resolver.py    # Fuzzy deduplication (thefuzz)
│   ├── graph/
│   │   ├── schema.py            # Constraints, indexes, init
│   │   ├── builder.py           # Neo4j graph builder
│   │   └── queries.py           # Cypher queries (search, paths, family)
│   ├── embeddings/
│   │   └── vectorizer.py        # OpenAI embeddings + vector indexes
│   └── rag/
│       ├── retriever.py         # Hybrid retriever (vector + graph)
│       └── generator.py         # LLM answer generation (EN/RU)
├── ui/
│   └── i18n.py                  # Translations (EN/RU, 100+ keys)
├── data/
│   ├── characters_seed.json     # 80+ curated character seeds
│   └── ramayana_griffith.txt    # Downloaded text (2.4 MB)
└── tests/                       # 110 tests across 16 modules
    ├── conftest.py              # Fixtures + stubs (no external deps)
    ├── test_parser.py
    ├── test_entity_extractor.py
    ├── test_relationship_extractor.py
    └── ... (13 more test modules)
```

## How It Works

### 1. Parsing

The parser processes Ralph T. H. Griffith's 1870-1874 English verse translation, splitting it by `BOOK` (Kanda) and `Canto` (Sarga) markers, then extracting individual stanzas. Result: **3,719 verses** across 6 Kandas and 493 Sargas.

### 2. LLM Entity Extraction

Verses are sent to GPT-4o-mini in batches of 20. The model extracts named entities (characters, locations, weapons, events, concepts) with descriptions. Alias resolution via fuzzy matching (thefuzz, threshold 85%) deduplicates variants like "Rama"/"Ráma"/"Ram".

Retry logic with exponential backoff (3 attempts, 2s/4s/8s delays) handles API timeouts.

### 3. Knowledge Graph

Extracted entities and relationships are stored in Neo4j with:
- **Uniqueness constraints** on entity names and verse IDs
- **Fulltext indexes** for entity and verse search
- **Vector indexes** for semantic similarity (1536-dim OpenAI embeddings)

### 4. Hybrid RAG

Three retrieval modes:
- **Vector** — cosine similarity search over verse embeddings
- **Graph** — entity search → relationship traversal → context assembly
- **Hybrid** — vector search → graph expansion from found entities → reranking

The generator produces answers with source citations and confidence scores. Russian language support adds an instruction to the system prompt while keeping entity names in original form.

## Neo4j Schema

**Node types:** Character, Location, Weapon, Event, Concept, Verse, Kanda, Sarga

**Relationship types:**
- Family: `FATHER_OF`, `MOTHER_OF`, `SON_OF`, `SPOUSE_OF`, `BROTHER_OF`, `SISTER_OF`
- Action: `FIGHTS`, `KILLS`, `KIDNAPS`, `RESCUES`, `WIELDS`, `TRAVELS_TO`
- Social: `ALLIES_WITH`, `SERVES`, `TEACHES`, `RULES`
- Structural: `MENTIONED_IN`, `BELONGS_TO`

## Data Source

[Griffith's Ramayana](https://www.gutenberg.org/ebooks/24869) — Ralph T. H. Griffith's English verse translation (1870-1874), Project Gutenberg. Public domain.

The 6 Kandas (Books):
1. **Bala Kanda** — Youth of Rama
2. **Ayodhya Kanda** — Exile from Ayodhya
3. **Aranya Kanda** — Forest life and Sita's abduction
4. **Kishkindha Kanda** — Alliance with the monkeys
5. **Sundara Kanda** — Hanuman's journey to Lanka
6. **Yuddha Kanda** — The great battle

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| LLM | OpenAI GPT-4o-mini (extraction, RAG) |
| Embeddings | OpenAI text-embedding-3-small (1536 dim) |
| Graph DB | Neo4j 5 Community (graph + vector storage) |
| UI | Streamlit |
| Alias Resolution | thefuzz (Levenshtein distance) |
| CI/CD | GitHub Actions (Python 3.11/3.12/3.13 + ruff) |
| Tests | pytest (110 tests) |

## Configuration

All settings via `.env` file (Pydantic Settings):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key (required) |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `ramayana_kg_2026` | Neo4j password |
| `NEO4J_DATABASE` | `ramayana` | Neo4j database name |
| `LLM_MODEL` | `gpt-4o-mini` | Model for extraction/RAG |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `EXTRACTION_BATCH_SIZE` | `20` | Verses per LLM call |

## Tests

```bash
# Run all 110 tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=ramayana_kg --cov-report=term-missing

# Lint
ruff check ramayana_kg/ tests/
```

Tests run without external dependencies (Neo4j, OpenAI stubs in conftest.py).

## Cost Estimate

| Operation | Cost |
|-----------|------|
| Entity extraction (3719 verses) | ~$0.50–1.00 |
| Relationship extraction | ~$0.30–0.50 |
| Embeddings (3719 verses + 944 entities) | ~$0.02 |
| RAG query (single) | ~$0.001 |

## License

MIT
