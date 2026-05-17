"""Integration tests for /api/articles endpoints."""
from app.core.models import Article


class TestListArticles:
    def test_empty_list(self, client, mock_repo):
        mock_repo.list_articles.return_value = []
        resp = client.get("/api/articles/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_articles(self, client, mock_repo):
        mock_repo.list_articles.return_value = [
            Article(id=1, feed_id=1, url="https://a.com/1", title="Article 1"),
            Article(id=2, feed_id=1, url="https://a.com/2", title="Article 2"),
        ]
        data = client.get("/api/articles/").json()
        assert len(data) == 2
        assert data[0]["title"] == "Article 1"

    def test_article_shape(self, client, mock_repo):
        mock_repo.list_articles.return_value = [
            Article(id=1, feed_id=1, url="https://a.com/1", title="T")
        ]
        article = client.get("/api/articles/").json()[0]
        for key in ("id", "feed_id", "url", "title", "content", "summary", "topic", "is_read"):
            assert key in article

    def test_filters_by_feed_id(self, client, mock_repo):
        mock_repo.list_articles.return_value = []
        client.get("/api/articles/?feed_id=5")
        mock_repo.list_articles.assert_called_once_with(
            feed_id=5, topic=None, limit=50, offset=0
        )

    def test_filters_by_topic(self, client, mock_repo):
        mock_repo.list_articles.return_value = []
        client.get("/api/articles/?topic=DevOps")
        mock_repo.list_articles.assert_called_once_with(
            feed_id=None, topic="DevOps", limit=50, offset=0
        )

    def test_pagination_limit_and_offset(self, client, mock_repo):
        mock_repo.list_articles.return_value = []
        client.get("/api/articles/?limit=10&offset=20")
        mock_repo.list_articles.assert_called_once_with(
            feed_id=None, topic=None, limit=10, offset=20
        )

    def test_rejects_limit_above_max(self, client):
        assert client.get("/api/articles/?limit=201").status_code == 422

    def test_rejects_negative_offset(self, client):
        assert client.get("/api/articles/?offset=-1").status_code == 422

    def test_rejects_zero_limit(self, client):
        assert client.get("/api/articles/?limit=0").status_code == 422


class TestGetArticle:
    def test_returns_article(self, client, mock_repo):
        mock_repo.get_article.return_value = Article(
            id=7, feed_id=1, url="https://a.com/7", title="Python tips"
        )
        resp = client.get("/api/articles/7")
        assert resp.status_code == 200
        assert resp.json()["id"] == 7
        assert resp.json()["title"] == "Python tips"

    def test_returns_404_when_not_found(self, client, mock_repo):
        mock_repo.get_article.return_value = None
        resp = client.get("/api/articles/999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Article not found"


class TestMarkAsRead:
    def test_marks_article_read_returns_204(self, client, mock_repo):
        mock_repo.get_article.return_value = Article(
            id=1, feed_id=1, url="https://a.com/1", title="T"
        )
        assert client.patch("/api/articles/1/read").status_code == 204

    def test_calls_repo_mark_as_read(self, client, mock_repo):
        mock_repo.get_article.return_value = Article(
            id=1, feed_id=1, url="https://a.com/1", title="T"
        )
        client.patch("/api/articles/1/read")
        mock_repo.mark_as_read.assert_called_once_with(1)

    def test_returns_404_when_not_found(self, client, mock_repo):
        mock_repo.get_article.return_value = None
        assert client.patch("/api/articles/999/read").status_code == 404


class TestDeleteArticle:
    def test_soft_deletes_article_returns_204(self, client, mock_repo):
        mock_repo.get_article.return_value = Article(
            id=1, feed_id=1, url="https://a.com/1", title="T"
        )
        assert client.delete("/api/articles/1").status_code == 204

    def test_calls_repo_delete(self, client, mock_repo):
        mock_repo.get_article.return_value = Article(
            id=1, feed_id=1, url="https://a.com/1", title="T"
        )
        client.delete("/api/articles/1")
        mock_repo.delete_article.assert_called_once_with(1)

    def test_returns_404_when_not_found(self, client, mock_repo):
        mock_repo.get_article.return_value = None
        assert client.delete("/api/articles/999").status_code == 404
