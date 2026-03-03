"""Configuration via Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"
    embedding_dimensions: int = 1536

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "ramayana_kg_2026"
    neo4j_database: str = "ramayana"

    # Extraction
    extraction_batch_size: int = 20
    extraction_max_retries: int = 3
    alias_fuzzy_threshold: float = 0.85

    # Retrieval
    top_k_vector: int = 20
    top_k_final: int = 5
    graph_depth: int = 2

    # Generation
    max_context_tokens: int = 4000
    temperature: float = 0.3

    # Data
    gutenberg_url: str = "https://www.gutenberg.org/ebooks/24869.txt.utf-8"
    data_dir: str = "data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
