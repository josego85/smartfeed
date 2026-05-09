from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, relationship

from ..core.config import settings


class Base(DeclarativeBase):
    pass


_SEED_TOPICS: list[dict] = [
    {
        "name": "Artificial Intelligence & Machine Learning",
        "description": (
            "artificial intelligence machine learning deep learning neural network large language model "
            "LLM GPT ChatGPT OpenAI Anthropic Claude Gemini Llama model training transformer "
            "NLP natural language processing computer vision AI research foundation model "
            "diffusion model reinforcement learning AI assistant benchmark fine-tuning"
        ),
    },
    {
        "name": "Web Development & Frontend",
        "description": (
            "web development frontend backend JavaScript TypeScript React Vue Angular CSS HTML "
            "Next.js Tailwind REST API GraphQL Node.js web framework browser UI design UX "
            "web performance SPA server-side rendering full stack developer web app"
        ),
    },
    {
        "name": "DevOps & Infrastructure",
        "description": (
            "DevOps infrastructure cloud computing AWS Azure Google Cloud Kubernetes Docker container "
            "CI CD pipeline deployment monitoring Terraform Ansible SRE reliability scalability "
            "microservices serverless platform engineering GitOps observability logging"
        ),
    },
    {
        "name": "Programming Languages & Tooling",
        "description": (
            "programming language Python Go Rust Java C++ Swift Kotlin compiler interpreter "
            "IDE developer tools package manager SDK framework software engineering code quality "
            "testing debugging refactoring software architecture design patterns API library"
        ),
    },
    {
        "name": "Cybersecurity",
        "description": (
            "cybersecurity information security hacking data breach ransomware malware phishing "
            "network security vulnerability CVE zero-day encryption penetration testing "
            "CISO threat intelligence exploit firewall authentication privacy GDPR attack defense"
        ),
    },
    {
        "name": "Open Source & Linux",
        "description": (
            "open source Linux GitHub free software GPL license open source project "
            "Linux distribution Ubuntu Debian Fedora kernel bash community software "
            "git repository contribution fork pull request open source maintainer"
        ),
    },
    {
        "name": "Hardware & Electronics",
        "description": (
            "hardware electronics CPU GPU processor chip semiconductor FPGA embedded systems "
            "IoT Internet of Things Arduino Raspberry Pi circuit PCB electronics engineering "
            "Intel AMD ARM RISC-V robotics 3D printing sensors microcontroller"
        ),
    },
    {
        "name": "Science & Research",
        "description": (
            "science research scientific study academic paper physics biology chemistry "
            "mathematics quantum computing space astronomy neuroscience genomics "
            "climate science technology research innovation breakthrough experiment peer review"
        ),
    },
]


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
        for topic in _SEED_TOPICS:
            conn.execute(
                text(
                    "INSERT INTO topics (name, description) VALUES (:name, :description)"
                    " ON CONFLICT (name) DO NOTHING"
                ),
                topic,
            )
        conn.commit()

        conn.execute(text(
            "ALTER TABLE articles ADD COLUMN IF NOT EXISTS"
            " topic_id INTEGER REFERENCES topics(id)"
        ))
        conn.commit()

        # Migrate string topics → topic_id and drop old column (only if column still exists)
        conn.execute(text("""
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
        """))
        conn.commit()
