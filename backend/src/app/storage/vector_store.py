from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.interfaces import VectorStore
from ..core.models import SearchResult
from ..processing.embeddings import embed
from .database import ArticleORM, engine


class PgVectorStore(VectorStore):
    async def add(self, id: str, text: str, metadata: dict) -> None:
        vec = embed(text)
        with Session(engine) as session:
            orm = session.get(ArticleORM, int(id))
            if orm:
                orm.embedding = vec
                session.commit()

    async def search(self, query: str, n_results: int = 10) -> list[SearchResult]:
        vec = embed(query)
        stmt = (
            select(
                ArticleORM,
                ArticleORM.embedding.cosine_distance(vec).label("distance"),
            )
            .where(ArticleORM.embedding.is_not(None))
            .order_by("distance")
            .limit(n_results)
        )
        with Session(engine) as session:
            rows = session.execute(stmt).all()
            return [
                SearchResult(
                    article_id=str(row.ArticleORM.id),
                    score=round(max(0.0, 1.0 - row.distance), 4),
                    document=row.ArticleORM.title,
                    metadata={
                        "title": row.ArticleORM.title,
                        "topic": row.ArticleORM.topic,
                        "url": row.ArticleORM.url,
                    },
                )
                for row in rows
            ]
