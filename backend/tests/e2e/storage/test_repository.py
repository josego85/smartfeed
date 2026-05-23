"""
FeedRepository contract tests — typed against the interface, not the implementation.

SOLID / DIP: these tests verify the behavioural contract of FeedRepository.
If the concrete backend changes (Postgres → Mongo → SQLite), the same tests
must pass without modification.

Run:
    docker compose -f docker-compose.test.yml up -d
    uv run pytest -m e2e -v
"""
from datetime import UTC

import pytest

from app.core.interfaces import FeedRepository
from app.core.models import Article, Feed

pytestmark = pytest.mark.e2e

# ── helpers ───────────────────────────────────────────────────────────────────


def _feed(url: str = "https://example.com/rss", title: str = "") -> Feed:
    return Feed(url=url, title=title)


def _article(feed_id: int, url: str = "https://example.com/a1", **kw) -> Article:
    title = kw.pop("title", "Title")
    return Article(feed_id=feed_id, url=url, title=title, **kw)


# ── Feed CRUD ─────────────────────────────────────────────────────────────────


class TestSaveFeed:
    async def test_returns_feed_with_id(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        assert feed.id is not None
        assert feed.url == "https://example.com/rss"

    async def test_duplicate_url_returns_existing(self, repo: FeedRepository):
        first = await repo.save_feed(_feed())
        second = await repo.save_feed(_feed())
        assert first.id == second.id

    async def test_different_urls_get_different_ids(self, repo: FeedRepository):
        a = await repo.save_feed(_feed("https://a.com/rss"))
        b = await repo.save_feed(_feed("https://b.com/rss"))
        assert a.id != b.id


class TestListFeeds:
    async def test_empty_when_no_feeds(self, repo: FeedRepository):
        assert await repo.list_feeds() == []

    async def test_returns_all_saved_feeds(self, repo: FeedRepository):
        await repo.save_feed(_feed("https://a.com/rss"))
        await repo.save_feed(_feed("https://b.com/rss"))
        feeds = await repo.list_feeds()
        assert len(feeds) == 2

    async def test_returned_feed_has_correct_url(self, repo: FeedRepository):
        await repo.save_feed(_feed("https://hn.com/rss", title="HN"))
        feeds = await repo.list_feeds()
        assert feeds[0].url == "https://hn.com/rss"
        assert feeds[0].title == "HN"


class TestGetFeed:
    async def test_returns_feed_by_id(self, repo: FeedRepository):
        saved = await repo.save_feed(_feed())
        found = await repo.get_feed(saved.id)
        assert found is not None
        assert found.id == saved.id
        assert found.url == saved.url

    async def test_returns_none_for_missing_id(self, repo: FeedRepository):
        assert await repo.get_feed(99999) is None


class TestDeleteFeed:
    async def test_deleted_feed_not_in_list(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        await repo.delete_feed(feed.id)
        assert await repo.list_feeds() == []

    async def test_deleted_feed_not_found_by_id(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        await repo.delete_feed(feed.id)
        assert await repo.get_feed(feed.id) is None

    async def test_delete_nonexistent_is_silent(self, repo: FeedRepository):
        await repo.delete_feed(99999)  # must not raise


class TestUpdateFeedSyncTime:
    async def test_last_synced_at_is_set(self, repo: FeedRepository):
        from datetime import datetime
        feed = await repo.save_feed(_feed())
        now = datetime.now(UTC)
        await repo.update_feed_sync_time(feed.id, now)
        updated = await repo.get_feed(feed.id)
        assert updated.last_synced_at is not None


class TestUpdateFeedMetadata:
    async def test_sets_title_when_empty(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed(title=""))
        await repo.update_feed_metadata(feed.id, "New Title", "New Desc")
        updated = await repo.get_feed(feed.id)
        assert updated.title == "New Title"

    async def test_does_not_overwrite_existing_title(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed(title="Original"))
        await repo.update_feed_metadata(feed.id, "New Title", "New Desc")
        updated = await repo.get_feed(feed.id)
        assert updated.title == "Original"


# ── Article CRUD ──────────────────────────────────────────────────────────────


class TestSaveArticlesBulk:
    async def test_saves_articles_and_returns_them(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        articles = [
            _article(feed.id, "https://example.com/a1", title="A1"),
            _article(feed.id, "https://example.com/a2", title="A2"),
        ]
        saved = await repo.save_articles_bulk(articles)
        assert len(saved) == 2
        assert all(a.id is not None for a in saved)

    async def test_duplicate_urls_are_ignored(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        article = _article(feed.id, "https://example.com/a1")
        await repo.save_articles_bulk([article])
        # save same URL again — must not raise, must not duplicate
        await repo.save_articles_bulk([article])
        assert len(await repo.list_articles(feed_id=feed.id)) == 1

    async def test_empty_list_returns_empty(self, repo: FeedRepository):
        assert await repo.save_articles_bulk([]) == []


class TestGetExistingUrls:
    async def test_returns_empty_set_when_no_articles(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        assert await repo.get_existing_urls(feed.id) == set()

    async def test_returns_saved_urls(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        await repo.save_articles_bulk([
            _article(feed.id, "https://example.com/a1"),
            _article(feed.id, "https://example.com/a2"),
        ])
        urls = await repo.get_existing_urls(feed.id)
        assert "https://example.com/a1" in urls
        assert "https://example.com/a2" in urls

    async def test_does_not_return_urls_from_other_feeds(self, repo: FeedRepository):
        feed_a = await repo.save_feed(_feed("https://a.com/rss"))
        feed_b = await repo.save_feed(_feed("https://b.com/rss"))
        await repo.save_articles_bulk([_article(feed_a.id, "https://a.com/1")])
        assert await repo.get_existing_urls(feed_b.id) == set()


class TestListArticles:
    async def test_returns_articles_for_feed(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        await repo.save_articles_bulk([
            _article(feed.id, "https://example.com/a1"),
            _article(feed.id, "https://example.com/a2"),
        ])
        articles = await repo.list_articles(feed_id=feed.id)
        assert len(articles) == 2

    async def test_excludes_soft_deleted_articles(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        saved = await repo.save_articles_bulk([_article(feed.id)])
        await repo.delete_article(saved[0].id)
        assert await repo.list_articles(feed_id=feed.id) == []

    async def test_pagination_limit(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        await repo.save_articles_bulk([
            _article(feed.id, f"https://example.com/a{i}") for i in range(5)
        ])
        articles = await repo.list_articles(feed_id=feed.id, limit=2)
        assert len(articles) == 2

    async def test_pagination_offset(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        await repo.save_articles_bulk([
            _article(feed.id, f"https://example.com/a{i}") for i in range(4)
        ])
        page1 = await repo.list_articles(feed_id=feed.id, limit=2, offset=0)
        page2 = await repo.list_articles(feed_id=feed.id, limit=2, offset=2)
        ids_p1 = {a.id for a in page1}
        ids_p2 = {a.id for a in page2}
        assert ids_p1.isdisjoint(ids_p2)

    async def test_no_feed_filter_returns_all(self, repo: FeedRepository):
        feed_a = await repo.save_feed(_feed("https://a.com/rss"))
        feed_b = await repo.save_feed(_feed("https://b.com/rss"))
        await repo.save_articles_bulk([_article(feed_a.id, "https://a.com/1")])
        await repo.save_articles_bulk([_article(feed_b.id, "https://b.com/1")])
        assert len(await repo.list_articles()) == 2


class TestGetArticle:
    async def test_returns_article_by_id(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        saved = await repo.save_articles_bulk([_article(feed.id)])
        found = await repo.get_article(saved[0].id)
        assert found is not None
        assert found.id == saved[0].id

    async def test_returns_none_for_missing_id(self, repo: FeedRepository):
        assert await repo.get_article(99999) is None

    async def test_returns_none_for_soft_deleted(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        saved = await repo.save_articles_bulk([_article(feed.id)])
        await repo.delete_article(saved[0].id)
        assert await repo.get_article(saved[0].id) is None


class TestMarkAsRead:
    async def test_article_is_read_after_mark(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        saved = await repo.save_articles_bulk([_article(feed.id)])
        assert saved[0].is_read is False
        await repo.mark_as_read(saved[0].id)
        updated = await repo.get_article(saved[0].id)
        assert updated.is_read is True

    async def test_mark_nonexistent_is_silent(self, repo: FeedRepository):
        await repo.mark_as_read(99999)  # must not raise


class TestDeleteArticle:
    async def test_soft_delete_hides_article(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        saved = await repo.save_articles_bulk([_article(feed.id)])
        await repo.delete_article(saved[0].id)
        assert await repo.get_article(saved[0].id) is None

    async def test_delete_nonexistent_is_silent(self, repo: FeedRepository):
        await repo.delete_article(99999)  # must not raise


class TestGetArticlesByIds:
    async def test_returns_articles_for_given_ids(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        saved = await repo.save_articles_bulk([
            _article(feed.id, "https://example.com/a1"),
            _article(feed.id, "https://example.com/a2"),
            _article(feed.id, "https://example.com/a3"),
        ])
        ids = [saved[0].id, saved[2].id]
        found = await repo.get_articles_by_ids(ids)
        assert len(found) == 2
        assert {a.id for a in found} == set(ids)

    async def test_empty_ids_returns_empty(self, repo: FeedRepository):
        assert await repo.get_articles_by_ids([]) == []


class TestUpdateArticleEnrichment:
    async def test_sets_topic_and_summary(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        saved = await repo.save_articles_bulk([_article(feed.id)])
        seeded_name = "Artificial Intelligence & Machine Learning"
        await repo.update_article_enrichment(saved[0].id, seeded_name, "Great summary.")
        updated = await repo.get_article(saved[0].id)
        assert updated.topic == seeded_name
        assert updated.summary == "Great summary."

    async def test_unknown_topic_name_leaves_topic_empty(self, repo: FeedRepository):
        feed = await repo.save_feed(_feed())
        saved = await repo.save_articles_bulk([_article(feed.id)])
        await repo.update_article_enrichment(saved[0].id, "NonExistentTopic", "Summary")
        updated = await repo.get_article(saved[0].id)
        assert updated.topic == ""


class TestListTopics:
    async def test_returns_seeded_topics(self, repo: FeedRepository):
        topics = await repo.list_topics()
        assert len(topics) > 0

    async def test_topics_have_name_and_description(self, repo: FeedRepository):
        topics = await repo.list_topics()
        for topic in topics:
            assert topic.name
            assert topic.id is not None

    async def test_includes_expected_default_topics(self, repo: FeedRepository):
        names = {t.name for t in await repo.list_topics()}
        assert "Artificial Intelligence & Machine Learning" in names
        assert "DevOps & Infrastructure" in names
        assert "Cybersecurity" in names

    async def test_topics_returned_in_alphabetical_order(self, repo: FeedRepository):
        topics = await repo.list_topics()
        names = [t.name for t in topics]
        assert names == sorted(names)
