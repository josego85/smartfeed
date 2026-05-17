"""Integration tests for the health endpoint."""


class TestHealth:
    def test_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_returns_ok_payload(self, client):
        assert client.get("/health").json() == {"status": "ok"}
