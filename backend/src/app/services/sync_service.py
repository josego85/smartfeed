import asyncio
from datetime import datetime, timezone

from ..core.config import settings
from ..core.interfaces import FeedRepository, Summarizer, VectorStore
from ..core.models import Article, SyncResult
from ..ingestion.fetcher import fetch_feed
from ..processing.classifier import classify


class FeedSyncService:
    def __init__(
        self,
        repo: FeedRepository,
        vector_store: VectorStore,
        summarizer: Summarizer,
    ) -> None:
        self._repo = repo
        self._vs = vector_store
        self._summarizer = summarizer

    async def sync(self, feed_id: int) -> SyncResult:
        feed = await self._repo.get_feed(feed_id)
        if feed is None:
            raise ValueError(f"Feed {feed_id} not found")

        fetched = await fetch_feed(feed)
        existing = await self._repo.get_existing_urls(feed_id)
        new_articles = [a for a in fetched if a.url not in existing]

        saved: list[Article] = []
        if new_articles:
            sem = asyncio.Semaphore(settings.sync_concurrency)
            enriched = await asyncio.gather(
                *[self._enrich(a, sem) for a in new_articles]
            )
            saved = await self._repo.save_articles_bulk(list(enriched))
            await asyncio.gather(
                *[
                    self._vs.add(
                        id=str(a.id),
                        text=f"{a.title}\n\n{a.content}",
                        metadata={"title": a.title, "topic": a.topic, "url": a.url},
                    )
                    for a in saved
                    if a.id
                ]
            )

        await self._repo.update_feed_sync_time(feed_id, datetime.now(timezone.utc))

        return SyncResult(
            feed_id=feed_id,
            fetched=len(fetched),
            new=len(saved),
            skipped=len(fetched) - len(new_articles),
        )

    async def _enrich(self, article: Article, sem: asyncio.Semaphore) -> Article:
        async with sem:
            text = f"{article.title}\n\n{article.content}"
            article.topic, article.summary = await asyncio.gather(
                classify(text),
                self._summarizer.summarize(text),
            )
        return article
