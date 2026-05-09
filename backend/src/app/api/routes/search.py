from fastapi import APIRouter, Depends, Query

from ...core.config import settings
from ...core.interfaces import VectorStore
from ...core.models import SearchResult
from ..dependencies import get_vector_store

router = APIRouter()


@router.get("/", response_model=list[SearchResult])
async def semantic_search(
    q: str = Query(..., min_length=settings.search_min_query_length),
    n: int = Query(settings.search_default_results, ge=1, le=settings.search_max_results),
    vector_store: VectorStore = Depends(get_vector_store),
):
    return await vector_store.search(query=q, n_results=n)
