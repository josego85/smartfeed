from datetime import datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..core.interfaces import FeedRepository
from ..core.models import Article, Feed
from .database import ArticleORM, FeedORM, engine


def _to_feed(orm: FeedORM) -> Feed:
    return Feed(
        id=orm.id,
        url=orm.url,
        title=orm.title,
        description=orm.description,
        last_synced_at=orm.last_synced_at,
    )


def _to_article(orm: ArticleORM) -> Article:
    return Article(
        id=orm.id,
        feed_id=orm.feed_id,
        url=orm.url,
        title=orm.title,
        content=orm.content,
        summary=orm.summary,
        topic=orm.topic,
        published_at=orm.published_at,
        fetched_at=orm.fetched_at,
        is_read=orm.is_read,
    )


class PostgresRepository(FeedRepository):
    async def save_feed(self, feed: Feed) -> Feed:
        with Session(engine) as session:
            existing = session.query(FeedORM).filter_by(url=feed.url).first()
            if existing:
                return _to_feed(existing)
            orm = FeedORM(url=feed.url, title=feed.title, description=feed.description)
            session.add(orm)
            session.commit()
            session.refresh(orm)
            return _to_feed(orm)

    async def list_feeds(self) -> list[Feed]:
        with Session(engine) as session:
            return [_to_feed(f) for f in session.query(FeedORM).all()]

    async def get_feed(self, feed_id: int) -> Feed | None:
        with Session(engine) as session:
            orm = session.get(FeedORM, feed_id)
            return _to_feed(orm) if orm else None

    async def delete_feed(self, feed_id: int) -> None:
        with Session(engine) as session:
            orm = session.get(FeedORM, feed_id)
            if orm:
                session.delete(orm)
                session.commit()

    async def get_existing_urls(self, feed_id: int) -> set[str]:
        with Session(engine) as session:
            rows = (
                session.query(ArticleORM.url)
                .filter_by(feed_id=feed_id)
                .all()
            )
            return {row.url for row in rows}

    async def save_articles_bulk(self, articles: list[Article]) -> list[Article]:
        if not articles:
            return []
        with Session(engine) as session:
            rows = [
                {
                    "feed_id": a.feed_id,
                    "url": a.url,
                    "title": a.title,
                    "content": a.content,
                    "summary": a.summary,
                    "topic": a.topic,
                    "published_at": a.published_at,
                }
                for a in articles
            ]
            stmt = pg_insert(ArticleORM).values(rows).on_conflict_do_nothing(
                index_elements=["url"]
            )
            session.execute(stmt)
            session.commit()
            urls = [a.url for a in articles]
            saved = session.query(ArticleORM).filter(ArticleORM.url.in_(urls)).all()
            return [_to_article(orm) for orm in saved]

    async def update_feed_sync_time(self, feed_id: int, synced_at: datetime) -> None:
        with Session(engine) as session:
            orm = session.get(FeedORM, feed_id)
            if orm:
                orm.last_synced_at = synced_at
                session.commit()

    async def list_articles(
        self,
        feed_id: int | None = None,
        topic: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Article]:
        with Session(engine) as session:
            q = session.query(ArticleORM)
            if feed_id:
                q = q.filter_by(feed_id=feed_id)
            if topic:
                q = q.filter_by(topic=topic)
            rows = q.order_by(ArticleORM.fetched_at.desc()).offset(offset).limit(limit).all()
            return [_to_article(a) for a in rows]

    async def get_article(self, article_id: int) -> Article | None:
        with Session(engine) as session:
            orm = session.get(ArticleORM, article_id)
            return _to_article(orm) if orm else None

    async def mark_as_read(self, article_id: int) -> None:
        with Session(engine) as session:
            orm = session.get(ArticleORM, article_id)
            if orm:
                orm.is_read = True
                session.commit()
