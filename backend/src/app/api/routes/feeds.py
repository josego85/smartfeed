import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ...core.interfaces import FeedRepository
from ...core.models import Feed
from ...ingestion.fetcher import fetch_feed
from ...ingestion.scheduler import sync_all_feeds
from ..dependencies import get_repo, get_vector_store, get_summarizer

router = APIRouter()


class FeedCreate(BaseModel):
    url: str
    title: str = ""
    description: str = ""


@router.get("/", response_model=list[Feed])
async def list_feeds(repo: FeedRepository = Depends(get_repo)):
    return await repo.list_feeds()


@router.post("/", response_model=Feed, status_code=201)
async def add_feed(body: FeedCreate, repo: FeedRepository = Depends(get_repo)):
    feed = await repo.save_feed(Feed(url=body.url, title=body.title, description=body.description))
    return feed


@router.delete("/{feed_id}", status_code=204)
async def delete_feed(feed_id: int, repo: FeedRepository = Depends(get_repo)):
    feed = await repo.get_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    await repo.delete_feed(feed_id)


@router.post("/{feed_id}/sync", status_code=202)
async def sync_feed(
    feed_id: int,
    repo: FeedRepository = Depends(get_repo),
    vector_store=Depends(get_vector_store),
    summarizer=Depends(get_summarizer),
):
    feed = await repo.get_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    try:
        articles = await fetch_feed(feed)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Feed returned {exc.response.status_code}: {feed.url}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach feed: {exc}")
    for article in articles:
        from ...processing.classifier import classify
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
    return {"synced": len(articles)}
