"""Unit tests for Settings / pydantic-settings configuration."""
import pytest

from app.core.config import Settings


class TestSettings:
    def test_default_database_url(self):
        s = Settings()
        assert "postgresql" in s.database_url

    def test_default_redis_url(self):
        s = Settings()
        assert s.redis_url == "redis://localhost:6379"

    def test_database_url_env_override(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@remotehost:5432/mydb")
        s = Settings()
        assert "remotehost" in s.database_url

    def test_default_llm_provider_is_ollama(self):
        s = Settings()
        assert s.llm_provider == "ollama"

    def test_default_llm_model(self):
        s = Settings()
        assert s.llm_model == "llama3.2"

    def test_default_embedding_dim(self):
        s = Settings()
        assert s.embedding_dim == 768

    def test_default_embedding_model(self):
        s = Settings()
        assert s.embedding_model == "nomic-embed-text"

    def test_pagination_defaults(self):
        s = Settings()
        assert s.articles_default_limit == 50
        assert s.articles_max_limit == 200
        assert s.search_default_results == 10
        assert s.search_max_results == 50
        assert s.search_min_query_length == 2

    def test_processing_defaults(self):
        s = Settings()
        assert s.max_classify_chars == 2000
        assert s.max_summarize_chars == 4000
        assert s.sync_concurrency == 3

    def test_worker_defaults(self):
        s = Settings()
        assert s.worker_max_jobs == 10
        assert s.worker_job_timeout == 600

    def test_cors_origins_default(self):
        s = Settings()
        assert "http://localhost:3000" in s.cors_origins

    def test_extra_env_vars_are_ignored(self, monkeypatch):
        monkeypatch.setenv("TOTALLY_UNKNOWN_KEY", "value")
        s = Settings()  # must not raise
        assert not hasattr(s, "totally_unknown_key")

    def test_llm_env_override(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("LLM_MODEL", "claude-haiku-4-5")
        s = Settings()
        assert s.llm_provider == "anthropic"
        assert s.llm_model == "claude-haiku-4-5"
