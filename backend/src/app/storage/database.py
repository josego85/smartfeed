from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, relationship

from ..core.config import settings

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class Base(DeclarativeBase):
    pass


class FeedORM(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, default="")
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    articles = relationship("ArticleORM", back_populates="feed", cascade="all, delete-orphan")


class ArticleORM(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"), nullable=False)
    url = Column(String, unique=True, nullable=False)
    title = Column(String, default="")
    content = Column(Text, default="")
    summary = Column(Text, default="")
    topic = Column(String, default="")
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)
    feed = relationship("FeedORM", back_populates="articles")


engine = create_engine(settings.database_url, pool_pre_ping=True)


def init_db() -> None:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)
