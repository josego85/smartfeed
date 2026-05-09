from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from redis import asyncio as aioredis

from ...core.config import settings
from ...core.interfaces import FeedRepository, JobQueue
from ...core.models import Feed, SyncJobStatus
from ..dependencies import get_queue, get_repo

router = APIRouter()

_CHANNEL = "smartfeed:sync:events"


class FeedCreate(BaseModel):
    url: str
    title: str = ""
    description: str = ""


@router.get("/", response_model=list[Feed])
async def list_feeds(repo: FeedRepository = Depends(get_repo)):
    return await repo.list_feeds()


@router.post("/", response_model=Feed, status_code=201)
async def add_feed(body: FeedCreate, repo: FeedRepository = Depends(get_repo)):
    return await repo.save_feed(Feed(url=body.url, title=body.title, description=body.description))


@router.delete("/{feed_id}", status_code=204)
async def delete_feed(feed_id: int, repo: FeedRepository = Depends(get_repo)):
    feed = await repo.get_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    await repo.delete_feed(feed_id)


@router.post("/{feed_id}/sync", status_code=202, response_model=SyncJobStatus)
async def enqueue_sync(
    feed_id: int,
    repo: FeedRepository = Depends(get_repo),
    queue: JobQueue = Depends(get_queue),
):
    feed = await repo.get_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    job_id = await queue.enqueue_sync(feed_id)
    return SyncJobStatus(job_id=job_id, status="queued")


@router.get("/{feed_id}/sync-status", response_model=SyncJobStatus)
async def sync_status(
    feed_id: int,
    job_id: str,
    queue: JobQueue = Depends(get_queue),
):
    return await queue.get_status(job_id)


@router.get("/sync-events")
async def sync_events(request: Request):
    async def stream():
        client = aioredis.from_url(settings.redis_url)
        pubsub = client.pubsub()
        await pubsub.subscribe(_CHANNEL)
        try:
            yield ": connected\n\n"
            while not await request.is_disconnected():
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=settings.pubsub_timeout
                )
                if msg:
                    yield f"data: {msg['data'].decode()}\n\n"
                else:
                    yield ": ping\n\n"
        finally:
            await pubsub.unsubscribe()
            await pubsub.aclose()
            await client.aclose()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
