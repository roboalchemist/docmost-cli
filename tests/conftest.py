"""Pytest fixtures for Docmost CLI tests."""

from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from docmost.client import DocmostClient


@pytest.fixture
def cli_runner() -> CliRunner:
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config() -> dict[str, Any]:
    """Mock configuration dictionary."""
    return {
        "url": "https://docs.example.com",
        "default_format": "table",
        "default_space": None,
    }


@pytest.fixture
def mock_token() -> str:
    """Mock authentication token."""
    return "test-token-12345"


@pytest.fixture
def mock_load_config(mock_config: dict[str, Any]) -> Generator[MagicMock, None, None]:
    """Patch load_config to return mock configuration."""
    with patch("docmost.config.load_config", return_value=mock_config) as mock:
        yield mock


@pytest.fixture
def mock_get_token(mock_token: str) -> Generator[MagicMock, None, None]:
    """Patch get_token to return mock token."""
    with patch("docmost.auth.get_token", return_value=mock_token) as mock:
        yield mock


@pytest.fixture
def mock_auth(mock_load_config: MagicMock, mock_get_token: MagicMock) -> None:
    """Combined fixture that mocks both config and authentication."""
    pass


@pytest.fixture
def mock_client(mock_config: dict[str, Any], mock_token: str) -> DocmostClient:
    """Create a DocmostClient with mock credentials (no HTTP mocking)."""
    return DocmostClient(url=mock_config["url"], token=mock_token)


@pytest.fixture
def mock_docmost_client() -> Generator[MagicMock, None, None]:
    """Patch DocmostClient entirely with a mock.

    Use this when you want to test CLI logic without any HTTP calls.
    """
    with patch("docmost.client.DocmostClient") as mock_cls:
        mock_instance = MagicMock(spec=DocmostClient)
        mock_cls.return_value = mock_instance
        yield mock_instance
