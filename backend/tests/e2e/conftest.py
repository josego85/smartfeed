"""
E2E conftest — real PostgreSQL via docker-compose.test.yml.

How to run:
    docker compose -f docker-compose.test.yml up -d
    uv run pytest -m e2e
    docker compose -f docker-compose.test.yml down -v
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.interfaces import FeedRepository
from app.storage.postgres_repo import PostgresRepository

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://smartfeed:smartfeed@localhost:5433/smartfeed_test",
)

# ── session-scoped engine ─────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def test_engine():
    """
    Build a test engine, patch both module-level globals that reference it,
    initialize schema + seeds, and restore everything after the session.

    Why patch both?  postgres_repo imports `engine` by value at load time, so
    patching only database.engine would leave postgres_repo using the prod engine.
    """
    engine = create_engine(TEST_DB_URL, pool_pre_ping=True)

    try:
        with engine.connect():
            pass
    except OperationalError:
        pytest.skip(
            "Test DB unavailable — start it with: docker compose -f docker-compose.test.yml up -d"
        )

    import app.storage.database as db_mod

    _orig_db = db_mod.engine
    db_mod.engine = engine

    # init_db / _migrate use the module-level `engine` by name — now resolved
    # to our test engine because we patched the module globals above.
    # postgres_repo and vector_store access engine via `database.engine`, so
    # patching db_mod.engine is sufficient — no need to patch them separately.
    db_mod.init_db()

    yield engine

    engine.dispose()
    db_mod.engine = _orig_db


# ── per-test isolation ────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_tables(test_engine):
    """Truncate transactional data between tests; keep seeded topics."""
    yield
    with test_engine.connect() as conn:
        conn.execute(text("TRUNCATE feeds RESTART IDENTITY CASCADE"))
        conn.commit()


# ── dependency-inverted repo fixture ─────────────────────────────────────────


@pytest.fixture
def repo(test_engine) -> FeedRepository:
    """
    Typed as FeedRepository (the interface), not PostgresRepository.
    SOLID / DIP: tests are written against the contract, not the concrete type.
    Swapping the implementation requires zero test changes.
    """
    return PostgresRepository()
