import asyncio

from arq import cron
from arq.connections import RedisSettings

from ..core.config import settings
from ..core.models import FeedStatus, SyncJobEvent, SyncResult
from ..ingestion.fetcher import PermanentFetchError
from ..processing.classifier import LLMClassifier
from ..processing.summarizer import LiteLLMSummarizer
from ..services.sync_service import FeedSyncService
from ..storage.postgres_repo import PostgresRepository
from ..storage.vector_store import PgVectorStore

_PERMANENT_STATUS_MAP = {
    0: FeedStatus.NOT_FOUND,  # invalid URL (no protocol, malformed)
    403: FeedStatus.FORBIDDEN,
    404: FeedStatus.NOT_FOUND,
    410: FeedStatus.NOT_FOUND,
    451: FeedStatus.FORBIDDEN,
}

_CHANNEL = "smartfeed:sync:events"


async def _publish(redis, event: SyncJobEvent) -> None:
    """Publish a sync event to Redis Pub/Sub, guarded against task cancellation."""
    try:
        await asyncio.shield(redis.publish(_CHANNEL, event.model_dump_json()))
    except asyncio.CancelledError:
        pass


async def sync_feed_job(ctx: dict, feed_id: int) -> dict:
    """Fast path: fetch and store raw articles, then enqueue enrichment."""
    service: FeedSyncService = ctx["sync_service"]
    repo: PostgresRepository = ctx["repo"]
    result: SyncResult | None = None
    error: str | None = None
    status = "failed"

    try:
        result, new_ids = await service.sync(feed_id)
        await repo.update_feed_status(feed_id, FeedStatus.ACTIVE)
        status = "complete"
        if new_ids:
            await ctx["redis"].enqueue_job("enrich_articles_job", feed_id, new_ids)
        return result.model_dump()
    except PermanentFetchError as exc:
        # Server explicitly rejects us — no point retrying. Persist the status and
        # let the job complete cleanly so ARQ does not schedule a retry.
        error = str(exc)
        feed_status = _PERMANENT_STATUS_MAP.get(exc.http_status, FeedStatus.UNREACHABLE)
        await repo.update_feed_status(feed_id, feed_status, error)
        return {"feed_id": feed_id, "fetched": 0, "new": 0, "skipped": 0}
    except Exception as exc:
        error = str(exc)
        await repo.update_feed_status(feed_id, FeedStatus.UNREACHABLE, error)
        raise  # transient — ARQ will retry
    finally:
        await _publish(
            ctx["redis"],
            SyncJobEvent(
                job_id=ctx["job_id"],
                feed_id=feed_id,
                status=status,
                result=result,
                error=error,
            ),
        )


async def enrich_articles_job(ctx: dict, feed_id: int, article_ids: list[int]) -> None:
    """Slow path: classify, summarize, and embed articles in the background.

    Publishes an 'enriched' SSE event on completion so the frontend refetches articles.
    Failures are silent — articles remain visible without topic/summary.
    """
    service: FeedSyncService = ctx["sync_service"]
    try:
        await service.enrich(article_ids)
    except Exception:
        pass
    finally:
        await _publish(
            ctx["redis"],
            SyncJobEvent(
                job_id=ctx["job_id"],
                feed_id=feed_id,
                status="enriched",
            ),
        )


_SKIP_STATUSES = {FeedStatus.FORBIDDEN, FeedStatus.NOT_FOUND}


async def sync_all_feeds_job(ctx: dict) -> None:
    feeds = await ctx["repo"].list_feeds()
    for feed in feeds:
        if feed.id is not None and feed.status not in _SKIP_STATUSES:
            await ctx["redis"].enqueue_job("sync_feed_job", feed.id)


async def startup(ctx: dict) -> None:
    repo = PostgresRepository()
    ctx["repo"] = repo
    ctx["sync_service"] = FeedSyncService(
        repo, PgVectorStore(), LiteLLMSummarizer(), LLMClassifier()
    )


async def shutdown(ctx: dict) -> None:
    pass


class WorkerSettings:
    functions = [sync_feed_job, enrich_articles_job, sync_all_feeds_job]
    cron_jobs = [cron(sync_all_feeds_job, minute={0, 30})]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = settings.worker_max_jobs
    job_timeout = settings.worker_job_timeout
