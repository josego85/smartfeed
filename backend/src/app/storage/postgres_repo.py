from datetime import datetime

from sqlalchemy.orm import Session

from ..core.interfaces import FeedRepository
from ..core.models import Article, Feed
from .database import ArticleORM, FeedORM, engine


def _to_feed(orm: FeedORM) -> Feed:
    return Feed(id=orm.id, url=orm.url, title=orm.title, description=orm.description)


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

    async def save_article(self, article: Article) -> Article:
        with Session(engine) as session:
            if session.query(ArticleORM).filter_by(url=article.url).first():
                return article
            orm = ArticleORM(
                feed_id=article.feed_id,
                url=article.url,
                title=article.title,
                content=article.content,
                summary=article.summary,
                topic=article.topic,
                published_at=article.published_at,
            )
            session.add(orm)
            session.commit()
            session.refresh(orm)
            return _to_article(orm)

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
