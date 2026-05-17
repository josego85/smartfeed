import asyncio
from datetime import datetime, timezone

from ..core.config import settings
from ..core.interfaces import Classifier, FeedRepository, Summarizer, VectorStore
from ..core.models import Article, SyncResult
from ..ingestion.fetcher import fetch_feed


class FeedSyncService:
    def __init__(
        self,
        repo: FeedRepository,
        vector_store: VectorStore,
        summarizer: Summarizer,
        classifier: Classifier,
    ) -> None:
        self._repo = repo
        self._vs = vector_store
        self._summarizer = summarizer
        self._classifier = classifier

    async def sync(self, feed_id: int) -> tuple[SyncResult, list[int]]:
        """Fetch and store raw articles. Fast path — no LLM calls.

        Returns (result, new_article_ids). Caller should enqueue enrich() for the IDs.
        """
        feed = await self._repo.get_feed(feed_id)
        if feed is None:
            raise ValueError(f"Feed {feed_id} not found")

        fetched = await fetch_feed(feed)
        if not feed.title and fetched.title:
            await self._repo.update_feed_metadata(feed_id, fetched.title, fetched.description)
        existing = await self._repo.get_existing_urls(feed_id)
        new_articles = [a for a in fetched.articles if a.url not in existing]

        saved: list[Article] = []
        if new_articles:
            saved = await self._repo.save_articles_bulk(new_articles)

        await self._repo.update_feed_sync_time(feed_id, datetime.now(timezone.utc))

        result = SyncResult(
            feed_id=feed_id,
            fetched=len(fetched.articles),
            new=len(saved),
            skipped=len(fetched.articles) - len(new_articles),
        )
        return result, [a.id for a in saved if a.id]

    async def enrich(self, article_ids: list[int]) -> None:
        """Classify, summarize, and embed articles. Slow path — runs in a background job."""
        articles = await self._repo.get_articles_by_ids(article_ids)
        if not articles:
            return

        topics = await self._repo.list_topics()
        sem = asyncio.Semaphore(settings.sync_concurrency)

        async def enrich_one(article: Article) -> None:
            async with sem:
                text = f"{article.title}\n\n{article.content}"
                topic, summary = await asyncio.gather(
                    self._classifier.classify(text, topics),
                    self._summarizer.summarize(text),
                )
                await self._repo.update_article_enrichment(article.id, topic, summary)
                await self._vs.add(
                    id=str(article.id),
                    text=text,
                    metadata={"title": article.title, "topic": topic, "url": article.url},
                )

        await asyncio.gather(*[enrich_one(a) for a in articles])
