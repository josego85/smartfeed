"""Unit tests for core Pydantic domain models."""

import pytest
from pydantic import ValidationError

from app.core.models import (
    Article,
    Feed,
    SearchResult,
    SyncJobEvent,
    SyncJobStatus,
    SyncResult,
    Topic,
)


class TestFeed:
    def test_minimal_creation(self):
        feed = Feed(url="https://example.com/rss")
        assert feed.url == "https://example.com/rss"
        assert feed.title == ""
        assert feed.description == ""
        assert feed.id is None
        assert feed.last_synced_at is None

    def test_full_creation(self, sample_feed):
        assert sample_feed.id == 1
        assert sample_feed.title == "Example Feed"

    def test_url_is_required(self):
        with pytest.raises(ValidationError):
            Feed()

    def test_id_optional(self):
        feed = Feed(url="https://example.com/rss")
        assert feed.id is None

    def test_last_synced_at_optional(self):
        feed = Feed(url="https://example.com/rss")
        assert feed.last_synced_at is None


class TestArticle:
    def test_minimal_creation(self):
        article = Article(feed_id=1, url="https://example.com/a", title="Hello")
        assert article.feed_id == 1
        assert article.url == "https://example.com/a"
        assert article.content == ""
        assert article.summary == ""
        assert article.topic == ""
        assert article.is_read is False
        assert article.id is None
        assert article.embedding_id is None

    def test_feed_id_required(self):
        with pytest.raises(ValidationError):
            Article(url="https://example.com/a", title="Hello")

    def test_url_required(self):
        with pytest.raises(ValidationError):
            Article(feed_id=1, title="Hello")

    def test_title_required(self):
        with pytest.raises(ValidationError):
            Article(feed_id=1, url="https://example.com/a")

    def test_published_at_optional(self):
        article = Article(feed_id=1, url="https://example.com/a", title="Hello")
        assert article.published_at is None

    def test_is_read_defaults_false(self):
        article = Article(feed_id=1, url="https://example.com/a", title="Hello")
        assert article.is_read is False


class TestTopic:
    def test_minimal_creation(self):
        topic = Topic(name="AI & ML")
        assert topic.name == "AI & ML"
        assert topic.description == ""
        assert topic.id is None

    def test_name_required(self):
        with pytest.raises(ValidationError):
            Topic()

    def test_full_creation(self, sample_topics):
        t = sample_topics[0]
        assert t.id == 1
        assert t.name == "AI & ML"
        assert "machine learning" in t.description


class TestSyncResult:
    def test_creation(self):
        r = SyncResult(feed_id=1, fetched=10, new=5, skipped=5)
        assert r.feed_id == 1
        assert r.fetched == 10
        assert r.new == 5
        assert r.skipped == 5

    def test_all_fields_required(self):
        with pytest.raises(ValidationError):
            SyncResult(feed_id=1, fetched=10)


class TestSyncJobStatus:
    def test_queued_status(self):
        s = SyncJobStatus(job_id="abc123", status="queued")
        assert s.job_id == "abc123"
        assert s.status == "queued"
        assert s.result is None
        assert s.error is None

    def test_complete_with_result(self):
        result = SyncResult(feed_id=1, fetched=3, new=2, skipped=1)
        s = SyncJobStatus(job_id="abc123", status="complete", result=result)
        assert s.result is not None
        assert s.result.new == 2

    def test_failed_with_error(self):
        s = SyncJobStatus(job_id="abc123", status="failed", error="Connection refused")
        assert s.error == "Connection refused"
        assert s.result is None

    def test_job_id_and_status_required(self):
        with pytest.raises(ValidationError):
            SyncJobStatus(status="queued")


class TestSearchResult:
    def test_creation(self):
        r = SearchResult(
            article_id="42",
            score=0.95,
            document="Python is great",
            metadata={"title": "Test", "url": "https://example.com"},
        )
        assert r.article_id == "42"
        assert r.score == 0.95
        assert r.metadata["title"] == "Test"

    def test_all_fields_required(self):
        with pytest.raises(ValidationError):
            SearchResult(article_id="1", score=0.9)


class TestSyncJobEvent:
    def test_creation(self):
        e = SyncJobEvent(job_id="j1", feed_id=3, status="complete")
        assert e.job_id == "j1"
        assert e.feed_id == 3
        assert e.status == "complete"
        assert e.result is None
        assert e.error is None

    def test_with_result(self):
        result = SyncResult(feed_id=3, fetched=5, new=3, skipped=2)
        e = SyncJobEvent(job_id="j1", feed_id=3, status="complete", result=result)
        assert e.result.new == 3
