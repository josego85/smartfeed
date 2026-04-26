from functools import lru_cache

from ..core.interfaces import FeedRepository, Summarizer, VectorStore
from ..processing.summarizer import LiteLLMSummarizer
from ..storage.postgres_repo import PostgresRepository
from ..storage.vector_store import PgVectorStore


@lru_cache
def get_repo() -> FeedRepository:
    return PostgresRepository()


@lru_cache
def get_vector_store() -> VectorStore:
    return PgVectorStore()


@lru_cache
def get_summarizer() -> Summarizer:
    return LiteLLMSummarizer()
