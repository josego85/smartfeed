from arq import ArqRedis
from arq.jobs import Job, JobStatus

from ..core.config import settings
from ..core.interfaces import JobQueue
from ..core.models import SyncJobStatus, SyncResult


class ArqJobQueue(JobQueue):
    def __init__(self, pool: ArqRedis) -> None:
        self._pool = pool

    async def enqueue_sync(self, feed_id: int) -> str:
        job = await self._pool.enqueue_job("sync_feed_job", feed_id)
        return job.job_id

    async def get_status(self, job_id: str) -> SyncJobStatus:
        job = Job(job_id, self._pool)
        status = await job.status()

        if status == JobStatus.not_found:
            return SyncJobStatus(job_id=job_id, status="not_found")

        if status in (JobStatus.queued, JobStatus.deferred):
            return SyncJobStatus(job_id=job_id, status="queued")

        if status == JobStatus.in_progress:
            return SyncJobStatus(job_id=job_id, status="in_progress")

        # complete — puede ser éxito o excepción
        try:
            data = await job.result(timeout=settings.job_result_timeout)
            return SyncJobStatus(
                job_id=job_id,
                status="complete",
                result=SyncResult(**data),
            )
        except Exception as exc:
            return SyncJobStatus(job_id=job_id, status="failed", error=str(exc))
