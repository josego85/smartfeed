from abc import ABC, abstractmethod
from datetime import datetime

from .models import Article, Feed, FeedStatus, SearchResult, SyncJobStatus, Topic


class FeedRepository(ABC):
    @abstractmethod
    async def save_feed(self, feed: Feed) -> Feed:
        pass

    @abstractmethod
    async def list_feeds(self) -> list[Feed]:
        pass

    @abstractmethod
    async def get_feed(self, feed_id: int) -> Feed | None:
        pass

    @abstractmethod
    async def save_articles_bulk(self, articles: list[Article]) -> list[Article]:
        pass

    @abstractmethod
    async def get_existing_urls(self, feed_id: int) -> set[str]:
        pass

    @abstractmethod
    async def update_feed_sync_time(self, feed_id: int, synced_at: datetime) -> None:
        pass

    @abstractmethod
    async def update_feed_metadata(self, feed_id: int, title: str, description: str) -> None:
        pass

    @abstractmethod
    async def update_feed_status(
        self, feed_id: int, status: FeedStatus, last_error: str | None = None
    ) -> None:
        pass

    @abstractmethod
    async def list_articles(
        self,
        feed_id: int | None = None,
        topic: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Article]:
        pass

    @abstractmethod
    async def get_article(self, article_id: int) -> Article | None:
        pass

    @abstractmethod
    async def mark_as_read(self, article_id: int) -> None:
        pass

    @abstractmethod
    async def delete_article(self, article_id: int) -> None:
        pass

    @abstractmethod
    async def delete_feed(self, feed_id: int) -> None:
        pass

    @abstractmethod
    async def get_articles_by_ids(self, article_ids: list[int]) -> list[Article]:
        pass

    @abstractmethod
    async def update_article_enrichment(self, article_id: int, topic: str, summary: str) -> None:
        pass

    @abstractmethod
    async def list_topics(self) -> list[Topic]:
        pass


class VectorStore(ABC):
    @abstractmethod
    async def add(self, id: str, text: str, metadata: dict) -> None:
        pass

    @abstractmethod
    async def search(self, query: str, n_results: int = 10) -> list[SearchResult]:
        pass


class Summarizer(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> str:
        pass


class Classifier(ABC):
    @abstractmethod
    async def classify(self, text: str, topics: list[Topic]) -> str:
        pass


class JobQueue(ABC):
    @abstractmethod
    async def enqueue_sync(self, feed_id: int) -> str:
        pass

    @abstractmethod
    async def get_status(self, job_id: str) -> SyncJobStatus:
        pass
