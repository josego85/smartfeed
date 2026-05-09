from fastapi import APIRouter, Depends

from ...core.interfaces import FeedRepository
from ...core.models import Topic
from ..dependencies import get_repo

router = APIRouter()


@router.get("/", response_model=list[Topic])
async def list_topics(repo: FeedRepository = Depends(get_repo)):
    return await repo.list_topics()
