from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Infrastructure ────────────────────────────────────────────────────────
    database_url: str = "postgresql://smartfeed:smartfeed@localhost:5432/smartfeed"
    redis_url: str = "redis://localhost:6379"

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    # ── HTTP ──────────────────────────────────────────────────────────────────
    http_timeout: int = 30

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768           # must match the embedding model output

    # ── Processing ────────────────────────────────────────────────────────────
    max_classify_chars: int = 2000     # chars fed to the classifier
    max_summarize_chars: int = 4000    # chars sent to the LLM summarizer
    sync_concurrency: int = 3          # parallel enrich tasks per sync job

    # ── API pagination ────────────────────────────────────────────────────────
    articles_default_limit: int = 50
    articles_max_limit: int = 200
    search_default_results: int = 10
    search_max_results: int = 50
    search_min_query_length: int = 2

    # ── Worker ────────────────────────────────────────────────────────────────
    worker_max_jobs: int = 10
    worker_job_timeout: int = 600      # seconds before a job is killed
    pubsub_timeout: float = 15.0       # seconds to wait for a Redis pub/sub message (SSE keepalive)
    job_result_timeout: int = 5        # seconds to wait when fetching a completed job result


settings = Settings()
