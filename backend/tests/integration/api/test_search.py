"""Integration tests for /api/search endpoint."""
from app.core.config import settings
from app.core.models import SearchResult


class TestSemanticSearch:
    def test_returns_200(self, client, mock_vector_store):
        mock_vector_store.search.return_value = []
        assert client.get("/api/search/?q=python").status_code == 200

    def test_returns_results(self, client, mock_vector_store):
        mock_vector_store.search.return_value = [
            SearchResult(
                article_id="1",
                score=0.95,
                document="Python article",
                metadata={"title": "Python", "url": "https://a.com/1"},
            )
        ]
        data = client.get("/api/search/?q=python").json()
        assert len(data) == 1
        assert data[0]["article_id"] == "1"
        assert data[0]["score"] == 0.95

    def test_returns_empty_list(self, client, mock_vector_store):
        mock_vector_store.search.return_value = []
        assert client.get("/api/search/?q=noresults").json() == []

    def test_result_shape(self, client, mock_vector_store):
        mock_vector_store.search.return_value = [
            SearchResult(
                article_id="2", score=0.8, document="Doc",
                metadata={"title": "T", "url": "https://a.com/2"},
            )
        ]
        item = client.get("/api/search/?q=test").json()[0]
        for key in ("article_id", "score", "document", "metadata"):
            assert key in item

    def test_requires_q_parameter(self, client):
        assert client.get("/api/search/").status_code == 422

    def test_rejects_query_below_min_length(self, client):
        # min_length is 2; single char must be rejected
        assert client.get("/api/search/?q=x").status_code == 422

    def test_passes_n_to_vector_store(self, client, mock_vector_store):
        mock_vector_store.search.return_value = []
        client.get("/api/search/?q=test&n=5")
        mock_vector_store.search.assert_called_once_with(query="test", n_results=5)

    def test_default_n_is_config_value(self, client, mock_vector_store):
        mock_vector_store.search.return_value = []
        client.get("/api/search/?q=test")
        mock_vector_store.search.assert_called_once_with(
            query="test", n_results=settings.search_default_results
        )

    def test_rejects_n_above_max(self, client):
        assert client.get("/api/search/?q=test&n=51").status_code == 422

    def test_rejects_n_zero(self, client):
        assert client.get("/api/search/?q=test&n=0").status_code == 422
