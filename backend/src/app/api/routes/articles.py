from fastapi import APIRouter, Depends, HTTPException, Query

from ...core.interfaces import FeedRepository
from ...core.models import Article
from ..dependencies import get_repo

router = APIRouter()


@router.get("/", response_model=list[Article])
async def list_articles(
    feed_id: int | None = Query(None),
    topic: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: FeedRepository = Depends(get_repo),
):
    return await repo.list_articles(feed_id=feed_id, topic=topic, limit=limit, offset=offset)


@router.get("/{article_id}", response_model=Article)
async def get_article(article_id: int, repo: FeedRepository = Depends(get_repo)):
    article = await repo.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/{article_id}/read", status_code=204)
async def mark_as_read(article_id: int, repo: FeedRepository = Depends(get_repo)):
    article = await repo.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    await repo.mark_as_read(article_id)
