from abc import ABC, abstractmethod
from datetime import datetime
from .models import Feed, Article, Topic, SearchResult, SyncJobStatus


class FeedRepository(ABC):
    @abstractmethod
    async def save_feed(self, feed: Feed) -> Feed: ...

    @abstractmethod
    async def list_feeds(self) -> list[Feed]: ...

    @abstractmethod
    async def get_feed(self, feed_id: int) -> Feed | None: ...

    @abstractmethod
    async def save_articles_bulk(self, articles: list[Article]) -> list[Article]: ...

    @abstractmethod
    async def get_existing_urls(self, feed_id: int) -> set[str]: ...

    @abstractmethod
    async def update_feed_sync_time(self, feed_id: int, synced_at: datetime) -> None: ...

    @abstractmethod
    async def list_articles(
        self,
        feed_id: int | None = None,
        topic: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Article]: ...

    @abstractmethod
    async def get_article(self, article_id: int) -> Article | None: ...

    @abstractmethod
    async def mark_as_read(self, article_id: int) -> None: ...

    @abstractmethod
    async def delete_article(self, article_id: int) -> None: ...

    @abstractmethod
    async def delete_feed(self, feed_id: int) -> None: ...

    @abstractmethod
    async def get_articles_by_ids(self, article_ids: list[int]) -> list[Article]: ...

    @abstractmethod
    async def update_article_enrichment(self, article_id: int, topic: str, summary: str) -> None: ...

    @abstractmethod
    async def list_topics(self) -> list[Topic]: ...


class VectorStore(ABC):
    @abstractmethod
    async def add(self, id: str, text: str, metadata: dict) -> None: ...

    @abstractmethod
    async def search(self, query: str, n_results: int = 10) -> list[SearchResult]: ...


class Summarizer(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> str: ...


class Classifier(ABC):
    @abstractmethod
    async def classify(self, text: str, topics: list[Topic]) -> str: ...


class JobQueue(ABC):
    @abstractmethod
    async def enqueue_sync(self, feed_id: int) -> str: ...

    @abstractmethod
    async def get_status(self, job_id: str) -> SyncJobStatus: ...
