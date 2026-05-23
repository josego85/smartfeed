from datetime import datetime

from pydantic import BaseModel


class Feed(BaseModel):
    id: int | None = None
    url: str
    title: str = ""
    description: str = ""
    created_at: datetime = datetime.utcnow()
    last_synced_at: datetime | None = None


class Article(BaseModel):
    id: int | None = None
    feed_id: int
    url: str
    title: str
    content: str = ""
    summary: str = ""
    topic: str = ""
    published_at: datetime | None = None
    fetched_at: datetime = datetime.utcnow()
    is_read: bool = False
    embedding_id: str | None = None


class Topic(BaseModel):
    id: int | None = None
    name: str
    description: str = ""


class SearchResult(BaseModel):
    article_id: str
    score: float
    document: str
    metadata: dict


class SyncResult(BaseModel):
    feed_id: int
    fetched: int
    new: int
    skipped: int


class SyncJobStatus(BaseModel):
    job_id: str
    status: str  # queued | in_progress | complete | failed | not_found
    result: SyncResult | None = None
    error: str | None = None


class SyncJobEvent(BaseModel):
    """Payload published to Redis Pub/Sub when a job reaches a terminal state."""

    job_id: str
    feed_id: int
    status: str  # complete | failed
    result: SyncResult | None = None
    error: str | None = None
