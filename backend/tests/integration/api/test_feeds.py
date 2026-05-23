"""Integration tests for /api/feeds endpoints."""

from app.core.models import Feed, SyncJobStatus, SyncResult


class TestListFeeds:
    def test_empty_list(self, client, mock_repo):
        mock_repo.list_feeds.return_value = []
        resp = client.get("/api/feeds/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_feeds(self, client, mock_repo):
        mock_repo.list_feeds.return_value = [
            Feed(id=1, url="https://hn.com/rss", title="HN"),
            Feed(id=2, url="https://lobste.rs/rss", title="Lobsters"),
        ]
        data = client.get("/api/feeds/").json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["title"] == "HN"
        assert data[1]["id"] == 2

    def test_feed_shape(self, client, mock_repo):
        mock_repo.list_feeds.return_value = [
            Feed(id=1, url="https://example.com/rss", title="Ex", description="Desc")
        ]
        feed = client.get("/api/feeds/").json()[0]
        for key in ("id", "url", "title", "description", "created_at", "last_synced_at"):
            assert key in feed


class TestAddFeed:
    def test_creates_feed_returns_201(self, client, mock_repo):
        mock_repo.save_feed.return_value = Feed(id=1, url="https://example.com/rss")
        resp = client.post("/api/feeds/", json={"url": "https://example.com/rss"})
        assert resp.status_code == 201

    def test_returned_feed_has_correct_url(self, client, mock_repo):
        mock_repo.save_feed.return_value = Feed(id=1, url="https://example.com/rss")
        data = client.post("/api/feeds/", json={"url": "https://example.com/rss"}).json()
        assert data["url"] == "https://example.com/rss"

    def test_url_is_required(self, client):
        assert client.post("/api/feeds/", json={}).status_code == 422

    def test_accepts_optional_title(self, client, mock_repo):
        mock_repo.save_feed.return_value = Feed(
            id=1, url="https://example.com/rss", title="My Feed"
        )
        data = client.post(
            "/api/feeds/", json={"url": "https://example.com/rss", "title": "My Feed"}
        ).json()
        assert data["title"] == "My Feed"

    def test_accepts_optional_description(self, client, mock_repo):
        mock_repo.save_feed.return_value = Feed(
            id=1, url="https://example.com/rss", description="Tech news"
        )
        data = client.post(
            "/api/feeds/", json={"url": "https://example.com/rss", "description": "Tech news"}
        ).json()
        assert data["description"] == "Tech news"


class TestDeleteFeed:
    def test_deletes_existing_feed_returns_204(self, client, mock_repo):
        mock_repo.get_feed.return_value = Feed(id=1, url="https://example.com/rss")
        assert client.delete("/api/feeds/1").status_code == 204

    def test_calls_repo_delete(self, client, mock_repo):
        mock_repo.get_feed.return_value = Feed(id=1, url="https://example.com/rss")
        client.delete("/api/feeds/1")
        mock_repo.delete_feed.assert_called_once_with(1)

    def test_returns_404_for_missing_feed(self, client, mock_repo):
        mock_repo.get_feed.return_value = None
        resp = client.delete("/api/feeds/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Feed not found"


class TestEnqueueSync:
    def test_enqueues_returns_202(self, client, mock_repo, mock_queue):
        mock_repo.get_feed.return_value = Feed(id=1, url="https://example.com/rss")
        mock_queue.enqueue_sync.return_value = "job-abc"
        resp = client.post("/api/feeds/1/sync")
        assert resp.status_code == 202

    def test_response_contains_job_id_and_status(self, client, mock_repo, mock_queue):
        mock_repo.get_feed.return_value = Feed(id=1, url="https://example.com/rss")
        mock_queue.enqueue_sync.return_value = "job-abc"
        data = client.post("/api/feeds/1/sync").json()
        assert data["job_id"] == "job-abc"
        assert data["status"] == "queued"

    def test_returns_404_for_missing_feed(self, client, mock_repo):
        mock_repo.get_feed.return_value = None
        assert client.post("/api/feeds/999/sync").status_code == 404


class TestSyncStatus:
    def test_returns_200_with_status(self, client, mock_queue):
        mock_queue.get_status.return_value = SyncJobStatus(job_id="job-1", status="complete")
        resp = client.get("/api/feeds/1/sync-status?job_id=job-1")
        assert resp.status_code == 200
        assert resp.json()["status"] == "complete"
        assert resp.json()["job_id"] == "job-1"

    def test_returns_in_progress_status(self, client, mock_queue):
        mock_queue.get_status.return_value = SyncJobStatus(job_id="job-2", status="in_progress")
        resp = client.get("/api/feeds/1/sync-status?job_id=job-2")
        assert resp.json()["status"] == "in_progress"

    def test_returns_result_when_complete(self, client, mock_queue):
        result = SyncResult(feed_id=1, fetched=5, new=3, skipped=2)
        mock_queue.get_status.return_value = SyncJobStatus(
            job_id="job-3", status="complete", result=result
        )
        data = client.get("/api/feeds/1/sync-status?job_id=job-3").json()
        assert data["result"]["new"] == 3
        assert data["result"]["skipped"] == 2
