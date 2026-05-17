"""Integration test fixtures — FastAPI TestClient with all I/O dependencies mocked."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_queue, get_repo, get_vector_store
from app.api.main import app
from app.core.models import SyncJobStatus


@pytest.fixture
def mock_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_feeds.return_value = []
    repo.list_articles.return_value = []
    repo.list_topics.return_value = []
    return repo


@pytest.fixture
def mock_vector_store() -> AsyncMock:
    vs = AsyncMock()
    vs.search.return_value = []
    return vs


@pytest.fixture
def mock_queue() -> AsyncMock:
    q = AsyncMock()
    q.enqueue_sync.return_value = "job-test-123"
    q.get_status.return_value = SyncJobStatus(job_id="job-test-123", status="queued")
    return q


@pytest.fixture
def client(mock_repo, mock_vector_store, mock_queue) -> TestClient:
    app.dependency_overrides[get_repo] = lambda: mock_repo
    app.dependency_overrides[get_vector_store] = lambda: mock_vector_store
    app.dependency_overrides[get_queue] = lambda: mock_queue

    fake_pool = MagicMock()
    fake_pool.aclose = AsyncMock()

    with patch("app.api.main.init_db"), \
         patch("app.api.main.create_pool", new=AsyncMock(return_value=fake_pool)):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()
