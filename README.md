# Ramayana Knowledge Graph

LLM-powered entity extraction + hybrid RAG (vector + graph) from Griffith's Ramayana translation.

## Architecture

```
Gutenberg Text → Parser → LLM Extraction → Neo4j KG → Hybrid RAG → Streamlit UI
                           (gpt-4o-mini)    (Vector + Graph)
```

**Key improvements over hardcoded approaches:**
- LLM entity extraction (vs hardcoded 44 characters)
- Hybrid RAG: vector similarity + graph traversal
- Multi-hop Cypher queries (shortest path, family tree, co-occurrence)
- 80+ curated character seeds with alias resolution

## Quick Start

```bash
# 1. Clone and install
cd ~/ramayana-kg
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Start Neo4j (Docker)
docker run -d --name ramayana-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/ramayana_kg_2026 \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5

# 4. Run pipeline
python run_pipeline.py all

# 5. Launch UI
./run_streamlit.sh
# Open http://localhost:8507
```

## CLI Commands

```bash
python run_pipeline.py download   # Download Gutenberg text
python run_pipeline.py parse      # Parse into verses
python run_pipeline.py extract    # LLM entity extraction
python run_pipeline.py build      # Build Neo4j graph
python run_pipeline.py embed      # Generate embeddings
python run_pipeline.py all        # Run full pipeline
python run_pipeline.py query "Who is Rama?" --mode hybrid
python run_pipeline.py stats      # Show graph statistics
python run_pipeline.py clear -y   # Clear database
```

## Streamlit UI (port 8507)

5 tabs:
1. **KG Explorer** — entity search, relationships, family tree, shortest path
2. **Hybrid Search & Q&A** — 3 modes (vector, graph, hybrid), sources, graph context
3. **Dashboard** — node/edge counts, distribution charts
4. **Co-occurrence** — character pair analysis, kanda filter
5. **Settings** — config, stats, pipeline controls, clear DB

## Neo4j Schema

**Nodes:** Character, Location, Weapon, Event, Concept, Verse, Kanda, Sarga

**Relationships:** FATHER_OF, SPOUSE_OF, BROTHER_OF, FIGHTS, ALLIES_WITH, RULES, TRAVELS_TO, WIELDS, KILLS, KIDNAPS, RESCUES, MENTIONED_IN, BELONGS_TO, SERVES, TEACHES

**Indexes:** uniqueness constraints, fulltext search, vector indexes (verse + entity)

## Data Source

[Griffith's Ramayana](https://www.gutenberg.org/ebooks/24869) (Project Gutenberg, public domain, 1870-1874). 6 Books, ~600 cantos.

## Tech Stack

- **Python 3.11+**
- **OpenAI** — gpt-4o-mini (extraction, RAG), text-embedding-3-small (vectors)
- **Neo4j 5** — graph + vector storage
- **Streamlit** — UI
- **thefuzz** — alias resolution
- **pytest** — 80+ tests

## Tests

```bash
pytest tests/ -v --cov=ramayana_kg
```

## Cost Estimate

- Entity extraction: ~$0.50-1.00 (full text)
- Embeddings: ~$0.02
- RAG queries: ~$0.001 each

## License

MIT
