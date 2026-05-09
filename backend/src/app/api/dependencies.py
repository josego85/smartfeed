from functools import lru_cache

from fastapi import Request

from ..core.interfaces import FeedRepository, JobQueue, Summarizer, VectorStore
from ..jobs.arq_queue import ArqJobQueue
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


async def get_queue(request: Request) -> JobQueue:
    return ArqJobQueue(request.app.state.redis_pool)
