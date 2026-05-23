from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from ..core.config import settings
from .seeds import SEED_TOPICS


class Base(DeclarativeBase):
    pass


class TopicORM(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    articles = relationship("ArticleORM", back_populates="topic")


class FeedORM(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, default="")
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_synced_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    last_error = Column(Text, nullable=True)
    articles = relationship("ArticleORM", back_populates="feed", cascade="all, delete-orphan")


class ArticleORM(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=False)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, default="")
    content = Column(Text, default="")
    summary = Column(Text, default="")
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    topic = relationship("TopicORM", back_populates="articles")
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    embedding = Column(Vector(settings.embedding_dim), nullable=True)
    feed = relationship("FeedORM", back_populates="articles")


engine = create_engine(settings.database_url, pool_pre_ping=True)


def init_db() -> None:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)
    _migrate()


def _migrate() -> None:
    """Idempotent migrations for schema changes not handled by create_all."""
    with engine.connect() as conn:
        for topic in SEED_TOPICS:
            conn.execute(
                text(
                    "INSERT INTO topics (name, description) VALUES (:name, :description)"
                    " ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description"
                ),
                topic,
            )
        conn.commit()

        conn.execute(
            text(
                "ALTER TABLE articles ADD COLUMN IF NOT EXISTS"
                " topic_id INTEGER REFERENCES topics(id)"
            )
        )
        conn.commit()

        # Migrate string topics → topic_id and drop old column (only if column still exists)
        conn.execute(
            text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'articles' AND column_name = 'topic'
                ) THEN
                    UPDATE articles
                    SET topic_id = (SELECT id FROM topics WHERE topics.name = articles.topic)
                    WHERE articles.topic IS NOT NULL
                      AND articles.topic != ''
                      AND articles.topic_id IS NULL;

                    ALTER TABLE articles DROP COLUMN topic;
                END IF;
            END $$;
        """)
        )
        conn.commit()

        conn.execute(
            text(
                "ALTER TABLE articles ADD COLUMN IF NOT EXISTS"
                " is_deleted BOOLEAN NOT NULL DEFAULT FALSE"
            )
        )
        conn.commit()

        conn.execute(
            text(
                "ALTER TABLE feeds ADD COLUMN IF NOT EXISTS"
                " status VARCHAR(20) NOT NULL DEFAULT 'active'"
            )
        )
        conn.execute(
            text("ALTER TABLE feeds ADD COLUMN IF NOT EXISTS last_error TEXT")
        )
        conn.commit()
