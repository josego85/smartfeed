from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..core.interfaces import FeedRepository, VectorStore, Summarizer
from ..processing.classifier import classify
from ..processing.embeddings import embed
from .fetcher import fetch_feed

scheduler = AsyncIOScheduler()


def start(repo: FeedRepository, vector_store: VectorStore, summarizer: Summarizer) -> None:
    scheduler.add_job(
        sync_all_feeds,
        trigger="interval",
        minutes=30,
        args=[repo, vector_store, summarizer],
        id="sync_feeds",
        replace_existing=True,
    )
    scheduler.start()


async def sync_all_feeds(
    repo: FeedRepository,
    vector_store: VectorStore,
    summarizer: Summarizer,
) -> None:
    feeds = await repo.list_feeds()
    for feed in feeds:
        articles = await fetch_feed(feed)
        for article in articles:
            text = f"{article.title}\n\n{article.content}"
            article.topic = classify(text)
            article.summary = await summarizer.summarize(text)
            saved = await repo.save_article(article)
            if saved.id:
                await vector_store.add(
                    id=str(saved.id),
                    text=text,
                    metadata={"title": article.title, "topic": article.topic, "url": article.url},
                )
