"""Tests for search commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from docmost.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_auth(tmp_path):
    """Mock authentication for tests."""
    config = {"url": "https://docs.example.com/api", "default_format": "json"}
    with patch("docmost.config.load_config", return_value=config):
        with patch("docmost.auth.get_token", return_value="test-token"):
            yield


class TestSearchCommand:
    """Tests for search command."""

    def test_search_pages(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Search pages and content."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "p1", "title": "Getting Started", "highlight": "...matched text..."},
                    {"id": "p2", "title": "API Reference", "highlight": "...API docs..."},
                ]
            }
        )

        result = runner.invoke(cli, ["search", "getting started"])
        assert result.exit_code == 0
        assert "Getting Started" in result.output

    def test_search_with_space_filter(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Search with space filter."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["search", "test query", "--space-id", "space-1"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b'"spaceId":"space-1"' in request.content

    def test_search_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Search with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["search", "query", "-p", "2", "-l", "10"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b'"page":2' in request.content
        assert b'"limit":10' in request.content

    def test_search_handles_results_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Search handles 'results' key."""
        httpx_mock.add_response(
            json={"results": [{"id": "p1", "title": "Result 1"}]}
        )

        result = runner.invoke(cli, ["search", "test"])
        assert result.exit_code == 0

    def test_search_no_results(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Search with no results."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["search", "nonexistent query"])
        assert result.exit_code == 0

    def test_search_error(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Search handles error."""
        httpx_mock.add_response(status_code=500, json={"message": "Search unavailable"})

        result = runner.invoke(cli, ["search", "test"])
        assert result.exit_code == 1
        assert "Search unavailable" in result.output


class TestSuggestCommand:
    """Tests for suggest (autocomplete) command."""

    def test_suggest_basic(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get search suggestions."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "p1", "title": "Getting Started", "type": "page"},
                    {"id": "p2", "title": "Get API Key", "type": "page"},
                ]
            }
        )

        result = runner.invoke(cli, ["suggest", "get"])
        assert result.exit_code == 0
        assert "Getting Started" in result.output

    def test_suggest_include_users(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Suggest with users included."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "u1", "title": "John Doe", "type": "user"},
                ]
            }
        )

        result = runner.invoke(cli, ["suggest", "john", "--include-users"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b'"includeUsers":true' in request.content

    def test_suggest_include_groups(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Suggest with groups included."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["suggest", "eng", "--include-groups"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b'"includeGroups":true' in request.content

    def test_suggest_include_both(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Suggest with both users and groups."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["suggest", "test", "-u", "-g"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b'"includeUsers":true' in request.content
        assert b'"includeGroups":true' in request.content

    def test_suggest_handles_suggestions_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Suggest handles 'suggestions' key."""
        httpx_mock.add_response(
            json={"suggestions": [{"id": "p1", "title": "Suggestion 1", "type": "page"}]}
        )

        result = runner.invoke(cli, ["suggest", "test"])
        assert result.exit_code == 0

    def test_suggest_error(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Suggest handles error."""
        httpx_mock.add_response(status_code=500, json={"message": "Service unavailable"})

        result = runner.invoke(cli, ["suggest", "test"])
        assert result.exit_code == 1
        assert "Service unavailable" in result.output
