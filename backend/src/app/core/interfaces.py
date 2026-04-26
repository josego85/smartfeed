from abc import ABC, abstractmethod
from .models import Feed, Article, SearchResult


class FeedRepository(ABC):
    @abstractmethod
    async def save_feed(self, feed: Feed) -> Feed: ...

    @abstractmethod
    async def list_feeds(self) -> list[Feed]: ...

    @abstractmethod
    async def get_feed(self, feed_id: int) -> Feed | None: ...

    @abstractmethod
    async def save_article(self, article: Article) -> Article: ...

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
    async def delete_feed(self, feed_id: int) -> None: ...


class VectorStore(ABC):
    @abstractmethod
    async def add(self, id: str, text: str, metadata: dict) -> None: ...

    @abstractmethod
    async def search(self, query: str, n_results: int = 10) -> list[SearchResult]: ...


class Summarizer(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> str: ...
