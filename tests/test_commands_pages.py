"""Tests for pages commands."""

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


class TestPagesCreateCommand:
    """Tests for pages create command."""

    def test_create_page(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Create a new page."""
        httpx_mock.add_response(json={"id": "page-123", "title": "My Page"})

        result = runner.invoke(
            cli, ["pages", "create", "--space-id", "space-1", "--title", "My Page"]
        )
        assert result.exit_code == 0
        assert "Page 'My Page' created" in result.output

    def test_create_page_with_content(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create page with content."""
        httpx_mock.add_response(json={"id": "page-1"})

        result = runner.invoke(
            cli,
            [
                "pages",
                "create",
                "-s",
                "space-1",
                "-t",
                "Test",
                "-c",
                "# Hello World",
            ],
        )
        assert result.exit_code == 0

    def test_create_page_with_parent(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create page with parent page ID."""
        httpx_mock.add_response(json={"id": "page-1"})

        result = runner.invoke(
            cli,
            ["pages", "create", "-s", "space-1", "-t", "Child", "-p", "parent-123"],
        )
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b"parentPageId=parent-123" in request.content

    def test_create_page_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create page handles error."""
        httpx_mock.add_response(status_code=400, json={"message": "Invalid space"})

        result = runner.invoke(
            cli, ["pages", "create", "-s", "invalid", "-t", "Test"]
        )
        assert result.exit_code == 1
        assert "Invalid space" in result.output


class TestPagesInfoCommand:
    """Tests for pages info command."""

    def test_page_info(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get page info."""
        httpx_mock.add_response(
            json={"id": "page-123", "title": "My Page", "content": "# Content"}
        )

        result = runner.invoke(cli, ["pages", "info", "page-123"])
        assert result.exit_code == 0
        assert "My Page" in result.output

    def test_page_info_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Page info handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "Page not found"})

        result = runner.invoke(cli, ["pages", "info", "nonexistent"])
        assert result.exit_code == 1
        assert "Page not found" in result.output


class TestPagesUpdateCommand:
    """Tests for pages update command."""

    def test_update_page_title(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update page title."""
        httpx_mock.add_response(json={"id": "page-1", "title": "New Title"})

        result = runner.invoke(
            cli, ["pages", "update", "page-1", "--title", "New Title"]
        )
        assert result.exit_code == 0
        assert "Page 'page-1' updated" in result.output

    def test_update_page_content(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update page content."""
        httpx_mock.add_response(json={"id": "page-1"})

        result = runner.invoke(
            cli, ["pages", "update", "page-1", "-c", "# Updated content"]
        )
        assert result.exit_code == 0

    def test_update_page_icon(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Update page icon."""
        httpx_mock.add_response(json={"id": "page-1"})

        result = runner.invoke(cli, ["pages", "update", "page-1", "--icon", "star"])
        assert result.exit_code == 0

    def test_update_page_cover_photo(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update page cover photo."""
        httpx_mock.add_response(json={"id": "page-1"})

        result = runner.invoke(
            cli, ["pages", "update", "page-1", "--cover-photo", "https://example.com/img.png"]
        )
        assert result.exit_code == 0


class TestPagesDeleteCommand:
    """Tests for pages delete command."""

    def test_delete_page_with_force(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete page with --force flag."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["pages", "delete", "page-1", "--force"])
        assert result.exit_code == 0
        assert "Page 'page-1' deleted" in result.output

    def test_delete_page_with_confirmation(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete page with confirmation."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["pages", "delete", "page-1"], input="y\n")
        assert result.exit_code == 0

    def test_delete_page_cancelled(self, runner: CliRunner, mock_auth) -> None:
        """Delete page cancelled by user."""
        result = runner.invoke(cli, ["pages", "delete", "page-1"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output


class TestPagesMoveCommand:
    """Tests for pages move command."""

    def test_move_page_to_parent(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Move page to new parent."""
        httpx_mock.add_response(json={"id": "page-1"})

        result = runner.invoke(
            cli, ["pages", "move", "page-1", "--parent-id", "new-parent"]
        )
        assert result.exit_code == 0
        assert "Page 'page-1' moved" in result.output

    def test_move_page_after(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Move page after another page."""
        httpx_mock.add_response(json={"id": "page-1"})

        result = runner.invoke(cli, ["pages", "move", "page-1", "--after", "page-2"])
        assert result.exit_code == 0

    def test_move_page_before(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Move page before another page."""
        httpx_mock.add_response(json={"id": "page-1"})

        result = runner.invoke(cli, ["pages", "move", "page-1", "--before", "page-2"])
        assert result.exit_code == 0


class TestPagesTreeCommand:
    """Tests for pages tree command."""

    def test_page_tree(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get page tree for a space."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "p1", "title": "Page 1", "parentPageId": None},
                    {"id": "p2", "title": "Page 2", "parentPageId": "p1"},
                ]
            }
        )

        result = runner.invoke(cli, ["pages", "tree", "space-1"])
        assert result.exit_code == 0
        assert "Page 1" in result.output

    def test_page_tree_handles_pages_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Page tree handles 'pages' key in response."""
        httpx_mock.add_response(
            json={"pages": [{"id": "p1", "title": "Root"}]}
        )

        result = runner.invoke(cli, ["pages", "tree", "space-1"])
        assert result.exit_code == 0


class TestPagesRecentCommand:
    """Tests for pages recent command."""

    def test_recent_pages(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get recent pages."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "p1", "title": "Recent 1", "updatedAt": "2024-01-15"},
                ]
            }
        )

        result = runner.invoke(cli, ["pages", "recent"])
        assert result.exit_code == 0
        assert "Recent 1" in result.output

    def test_recent_pages_filter_by_space(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Filter recent pages by space."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["pages", "recent", "--space-id", "space-1"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b"spaceId=space-1" in request.content

    def test_recent_pages_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Recent pages with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["pages", "recent", "-p", "2", "-l", "10"])
        assert result.exit_code == 0


class TestPagesExportCommand:
    """Tests for pages export command."""

    def test_export_page_to_stdout(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Export page to stdout."""
        httpx_mock.add_response(json={"content": "# My Page\n\nContent here"})

        result = runner.invoke(cli, ["pages", "export", "page-1"])
        assert result.exit_code == 0
        assert "# My Page" in result.output

    def test_export_page_as_html(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Export page as HTML."""
        httpx_mock.add_response(json={"content": "<h1>My Page</h1>"})

        result = runner.invoke(cli, ["pages", "export", "page-1", "-f", "html"])
        assert result.exit_code == 0
        assert "<h1>My Page</h1>" in result.output

    def test_export_page_to_file(
        self, runner: CliRunner, httpx_mock, mock_auth, tmp_path
    ) -> None:
        """Export page to file."""
        httpx_mock.add_response(json={"content": "# Exported content"})
        output_file = tmp_path / "exported.md"

        result = runner.invoke(
            cli, ["pages", "export", "page-1", "-o", str(output_file)]
        )
        assert result.exit_code == 0
        assert "Exported to" in result.output
        assert output_file.read_text() == "# Exported content"

    def test_export_page_handles_data_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Export handles 'data' key in response."""
        httpx_mock.add_response(json={"data": "Content from data key"})

        result = runner.invoke(cli, ["pages", "export", "page-1"])
        assert result.exit_code == 0
        assert "Content from data key" in result.output


class TestPagesHistoryCommand:
    """Tests for pages history command."""

    def test_page_history(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get page revision history."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "rev-1", "version": 1, "createdAt": "2024-01-01"},
                    {"id": "rev-2", "version": 2, "createdAt": "2024-01-02"},
                ]
            }
        )

        result = runner.invoke(cli, ["pages", "history", "page-1"])
        assert result.exit_code == 0
        assert "rev-1" in result.output

    def test_page_history_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Page history with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["pages", "history", "page-1", "-p", "2", "-l", "5"])
        assert result.exit_code == 0

    def test_page_history_handles_history_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Page history handles 'history' key."""
        httpx_mock.add_response(
            json={"history": [{"id": "rev-1", "version": 1}]}
        )

        result = runner.invoke(cli, ["pages", "history", "page-1"])
        assert result.exit_code == 0
