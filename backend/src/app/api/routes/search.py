from fastapi import APIRouter, Depends, Query

from ...core.interfaces import VectorStore
from ...core.models import SearchResult
from ..dependencies import get_vector_store

router = APIRouter()


@router.get("/", response_model=list[SearchResult])
async def semantic_search(
    q: str = Query(..., min_length=2),
    n: int = Query(10, ge=1, le=50),
    vector_store: VectorStore = Depends(get_vector_store),
):
    return await vector_store.search(query=q, n_results=n)
