"""Unit tests for FeedSyncService — all external I/O is mocked."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.core.models import Article, Feed, SyncResult, Topic
from app.ingestion.fetcher import FetchResult
from app.services.sync_service import FeedSyncService

_FETCH_MODULE = "app.services.sync_service.fetch_feed"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_existing_urls.return_value = set()
    repo.save_articles_bulk.return_value = []
    repo.list_topics.return_value = []
    return repo


@pytest.fixture
def mock_vector_store() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_summarizer() -> AsyncMock:
    s = AsyncMock()
    s.summarize.return_value = "A concise summary."
    return s


@pytest.fixture
def mock_classifier() -> AsyncMock:
    c = AsyncMock()
    c.classify.return_value = "AI & ML"
    return c


@pytest.fixture
def service(mock_repo, mock_vector_store, mock_summarizer, mock_classifier) -> FeedSyncService:
    return FeedSyncService(
        repo=mock_repo,
        vector_store=mock_vector_store,
        summarizer=mock_summarizer,
        classifier=mock_classifier,
    )


@pytest.fixture
def feed_no_title() -> Feed:
    return Feed(id=1, url="https://example.com/rss", title="")


@pytest.fixture
def feed_with_title() -> Feed:
    return Feed(id=1, url="https://example.com/rss", title="Existing Title")


@pytest.fixture
def fetch_result_two_articles() -> FetchResult:
    return FetchResult(
        title="Fetched Title",
        description="Fetched description",
        articles=[
            Article(id=None, feed_id=1, url="https://example.com/a1", title="A1", content="C1"),
            Article(id=None, feed_id=1, url="https://example.com/a2", title="A2", content="C2"),
        ],
    )


# ── sync() tests ──────────────────────────────────────────────────────────────


class TestSync:
    async def test_raises_for_unknown_feed(self, service, mock_repo):
        mock_repo.get_feed.return_value = None
        with pytest.raises(ValueError, match="Feed 99 not found"):
            await service.sync(99)

    async def test_returns_sync_result_and_new_ids(
        self, service, mock_repo, feed_no_title, fetch_result_two_articles
    ):
        mock_repo.get_feed.return_value = feed_no_title
        saved = [
            Article(id=10, feed_id=1, url="https://example.com/a1", title="A1"),
            Article(id=11, feed_id=1, url="https://example.com/a2", title="A2"),
        ]
        mock_repo.save_articles_bulk.return_value = saved

        with patch(_FETCH_MODULE, return_value=fetch_result_two_articles):
            result, new_ids = await service.sync(1)

        assert isinstance(result, SyncResult)
        assert result.feed_id == 1
        assert result.fetched == 2
        assert result.new == 2
        assert result.skipped == 0
        assert new_ids == [10, 11]

    async def test_skips_already_existing_articles(
        self, service, mock_repo, feed_no_title, fetch_result_two_articles
    ):
        mock_repo.get_feed.return_value = feed_no_title
        mock_repo.get_existing_urls.return_value = {"https://example.com/a1"}
        mock_repo.save_articles_bulk.return_value = [
            Article(id=11, feed_id=1, url="https://example.com/a2", title="A2"),
        ]

        with patch(_FETCH_MODULE, return_value=fetch_result_two_articles):
            result, _ = await service.sync(1)

        assert result.fetched == 2
        assert result.new == 1
        assert result.skipped == 1

    async def test_no_new_articles_skips_bulk_save(
        self, service, mock_repo, feed_no_title, fetch_result_two_articles
    ):
        mock_repo.get_feed.return_value = feed_no_title
        mock_repo.get_existing_urls.return_value = {
            "https://example.com/a1",
            "https://example.com/a2",
        }

        with patch(_FETCH_MODULE, return_value=fetch_result_two_articles):
            result, new_ids = await service.sync(1)

        mock_repo.save_articles_bulk.assert_not_called()
        assert new_ids == []
        assert result.new == 0

    async def test_updates_feed_metadata_when_title_is_empty(
        self, service, mock_repo, feed_no_title, fetch_result_two_articles
    ):
        mock_repo.get_feed.return_value = feed_no_title

        with patch(_FETCH_MODULE, return_value=fetch_result_two_articles):
            await service.sync(1)

        mock_repo.update_feed_metadata.assert_called_once_with(
            1, "Fetched Title", "Fetched description"
        )

    async def test_does_not_update_metadata_when_title_already_set(
        self, service, mock_repo, feed_with_title, fetch_result_two_articles
    ):
        mock_repo.get_feed.return_value = feed_with_title

        with patch(_FETCH_MODULE, return_value=fetch_result_two_articles):
            await service.sync(1)

        mock_repo.update_feed_metadata.assert_not_called()

    async def test_always_updates_sync_time(
        self, service, mock_repo, feed_no_title, fetch_result_two_articles
    ):
        mock_repo.get_feed.return_value = feed_no_title

        with patch(_FETCH_MODULE, return_value=fetch_result_two_articles):
            await service.sync(1)

        mock_repo.update_feed_sync_time.assert_called_once()
        feed_id_arg, synced_at_arg = mock_repo.update_feed_sync_time.call_args[0]
        assert feed_id_arg == 1
        assert isinstance(synced_at_arg, datetime)

    async def test_ids_of_saved_articles_returned(
        self, service, mock_repo, feed_no_title, fetch_result_two_articles
    ):
        mock_repo.get_feed.return_value = feed_no_title
        mock_repo.save_articles_bulk.return_value = [
            Article(id=5, feed_id=1, url="https://example.com/a1", title="A1"),
            Article(id=6, feed_id=1, url="https://example.com/a2", title="A2"),
        ]

        with patch(_FETCH_MODULE, return_value=fetch_result_two_articles):
            _, new_ids = await service.sync(1)

        assert new_ids == [5, 6]


# ── enrich() tests ────────────────────────────────────────────────────────────


class TestEnrich:
    async def test_empty_ids_returns_early(self, service, mock_repo):
        await service.enrich([])
        mock_repo.get_articles_by_ids.assert_called_once_with([])
        mock_repo.update_article_enrichment.assert_not_called()

    async def test_enriches_all_articles(self, service, mock_repo, mock_vector_store):
        mock_repo.get_articles_by_ids.return_value = [
            Article(id=1, feed_id=1, url="https://a.com/1", title="T1", content="C1"),
            Article(id=2, feed_id=1, url="https://a.com/2", title="T2", content="C2"),
        ]
        mock_repo.list_topics.return_value = [Topic(id=1, name="AI & ML")]

        await service.enrich([1, 2])

        assert mock_repo.update_article_enrichment.call_count == 2
        assert mock_vector_store.add.call_count == 2

    async def test_calls_classifier_with_title_and_content(
        self, service, mock_repo, mock_classifier
    ):
        mock_repo.get_articles_by_ids.return_value = [
            Article(id=5, feed_id=1, url="https://a.com/5", title="AI News", content="Neural nets"),
        ]
        mock_repo.list_topics.return_value = [Topic(id=1, name="AI & ML")]

        await service.enrich([5])

        call_text = mock_classifier.classify.call_args[0][0]
        assert "AI News" in call_text
        assert "Neural nets" in call_text

    async def test_calls_summarizer(self, service, mock_repo, mock_summarizer):
        mock_repo.get_articles_by_ids.return_value = [
            Article(id=3, feed_id=1, url="https://a.com/3", title="T", content="C"),
        ]
        mock_repo.list_topics.return_value = []

        await service.enrich([3])

        mock_summarizer.summarize.assert_called_once()

    async def test_stores_vector_with_correct_id(self, service, mock_repo, mock_vector_store):
        mock_repo.get_articles_by_ids.return_value = [
            Article(id=7, feed_id=1, url="https://a.com/7", title="Title", content="Content"),
        ]
        mock_repo.list_topics.return_value = []

        await service.enrich([7])

        call_kwargs = mock_vector_store.add.call_args[1]
        assert call_kwargs["id"] == "7"

    async def test_vector_metadata_includes_topic_from_classifier(
        self, service, mock_repo, mock_vector_store, mock_classifier
    ):
        mock_classifier.classify.return_value = "DevOps"
        mock_repo.get_articles_by_ids.return_value = [
            Article(id=8, feed_id=1, url="https://a.com/8", title="K8s", content="Pods"),
        ]
        mock_repo.list_topics.return_value = [Topic(id=3, name="DevOps")]

        await service.enrich([8])

        metadata = mock_vector_store.add.call_args[1]["metadata"]
        assert metadata["topic"] == "DevOps"

    async def test_topics_fetched_from_repo(self, service, mock_repo):
        mock_repo.get_articles_by_ids.return_value = [
            Article(id=1, feed_id=1, url="https://a.com/1", title="T", content="C"),
        ]
        topics = [Topic(id=1, name="AI & ML"), Topic(id=2, name="DevOps")]
        mock_repo.list_topics.return_value = topics

        await service.enrich([1])

        mock_repo.list_topics.assert_called_once()
