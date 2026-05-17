"""Integration tests for /api/topics endpoint."""
from app.core.models import Topic


class TestListTopics:
    def test_returns_empty_list(self, client, mock_repo):
        mock_repo.list_topics.return_value = []
        resp = client.get("/api/topics/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_topics(self, client, mock_repo, sample_topics):
        mock_repo.list_topics.return_value = sample_topics
        data = client.get("/api/topics/").json()
        assert len(data) == 3

    def test_topic_names(self, client, mock_repo, sample_topics):
        mock_repo.list_topics.return_value = sample_topics
        names = {t["name"] for t in client.get("/api/topics/").json()}
        assert "AI & ML" in names
        assert "Web Development" in names
        assert "DevOps" in names

    def test_topic_shape(self, client, mock_repo):
        mock_repo.list_topics.return_value = [
            Topic(id=1, name="AI & ML", description="machine learning")
        ]
        topic = client.get("/api/topics/").json()[0]
        assert topic["id"] == 1
        assert topic["name"] == "AI & ML"
        assert topic["description"] == "machine learning"
        for key in ("id", "name", "description"):
            assert key in topic
