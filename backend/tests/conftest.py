"""Shared pytest configuration.

Test layers (each has its own directory and marker):
  unit/         fast, isolated, no external services
  integration/  several components together; must not need PostgreSQL-specific features
  pgvector/     REQUIRE real PostgreSQL + pgvector; skipped unless TEST_DATABASE_URL is set
  e2e/          against a running deployment
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

TESTS_DIR = Path(__file__).parent
LAYERS = {"unit", "integration", "pgvector", "e2e"}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Mark tests by directory, and skip pgvector tests when no real database is configured."""
    pgvector_available = bool(os.environ.get("TEST_DATABASE_URL"))
    for item in items:
        layer = item.path.relative_to(TESTS_DIR).parts[0]
        if layer in LAYERS:
            item.add_marker(getattr(pytest.mark, layer))
        if item.get_closest_marker("pgvector") and not pgvector_available:
            item.add_marker(
                pytest.mark.skip(reason="requires real PostgreSQL+pgvector (set TEST_DATABASE_URL)")
            )


@pytest.fixture
def settings() -> Settings:
    # _env_file=None keeps a developer's local .env from leaking into tests.
    return Settings(
        _env_file=None,
        app_env="test",
        log_format="console",
        database_url="sqlite:///:memory:",
        jwt_secret="test-secret-key",
        cors_allowed_origins=["http://allowed.test"],
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))
