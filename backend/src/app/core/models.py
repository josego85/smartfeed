from datetime import datetime
from pydantic import BaseModel


class Feed(BaseModel):
    id: int | None = None
    url: str
    title: str = ""
    description: str = ""
    created_at: datetime = datetime.utcnow()


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
    name: str
    description: str


class SearchResult(BaseModel):
    article_id: str
    score: float
    document: str
    metadata: dict
