"""Root conftest — shared fixtures available to every test layer."""

from datetime import datetime

import pytest

from app.core.models import Article, Feed, Topic


@pytest.fixture
def sample_feed() -> Feed:
    return Feed(id=1, url="https://example.com/feed.xml", title="Example Feed", description="")


@pytest.fixture
def sample_article() -> Article:
    return Article(
        id=10,
        feed_id=1,
        url="https://example.com/article-1",
        title="Test Article",
        content="This is a test article about Python.",
        published_at=datetime(2024, 1, 15, 10, 0, 0),
    )


@pytest.fixture
def sample_topics() -> list[Topic]:
    return [
        Topic(id=1, name="AI & ML", description="machine learning, deep learning, neural networks"),
        Topic(id=2, name="Web Development", description="frontend, backend, html, css, javascript"),
        Topic(id=3, name="DevOps", description="kubernetes, docker, CI/CD, infrastructure"),
    ]
