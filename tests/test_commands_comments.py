"""Tests for comments commands."""

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


class TestCommentsListCommand:
    """Tests for comments list command."""

    def test_list_comments(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """List comments on a page."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "c1", "content": "Great page!", "creatorId": "u1"},
                    {"id": "c2", "content": "Needs revision", "creatorId": "u2"},
                ]
            }
        )

        result = runner.invoke(cli, ["comments", "list", "page-123"])
        assert result.exit_code == 0
        assert "Great page!" in result.output

    def test_list_comments_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List comments with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(
            cli, ["comments", "list", "page-123", "-p", "2", "-l", "10"]
        )
        assert result.exit_code == 0

    def test_list_comments_handles_comments_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List handles 'comments' key."""
        httpx_mock.add_response(
            json={"comments": [{"id": "c1", "content": "A comment"}]}
        )

        result = runner.invoke(cli, ["comments", "list", "page-123"])
        assert result.exit_code == 0

    def test_list_comments_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List comments handles error."""
        httpx_mock.add_response(status_code=404, json={"message": "Page not found"})

        result = runner.invoke(cli, ["comments", "list", "nonexistent"])
        assert result.exit_code == 1
        assert "Page not found" in result.output


class TestCommentsCreateCommand:
    """Tests for comments create command."""

    def test_create_comment(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Create a comment."""
        httpx_mock.add_response(json={"id": "new-comment", "content": "My comment"})

        result = runner.invoke(
            cli, ["comments", "create", "page-123", "--content", "My comment"]
        )
        assert result.exit_code == 0
        assert "Comment created" in result.output

    def test_create_comment_with_selection(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create comment with selection."""
        httpx_mock.add_response(json={"id": "c1"})

        result = runner.invoke(
            cli,
            [
                "comments",
                "create",
                "page-123",
                "-c",
                "Selected text comment",
                "-s",
                '{"start": 10, "end": 20}',
            ],
        )
        assert result.exit_code == 0

    def test_create_comment_reply(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create a reply to a comment."""
        httpx_mock.add_response(json={"id": "reply-1"})

        result = runner.invoke(
            cli,
            [
                "comments",
                "create",
                "page-123",
                "-c",
                "Reply content",
                "-p",
                "parent-comment-id",
            ],
        )
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b"parentCommentId=parent-comment-id" in request.content

    def test_create_comment_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create comment handles error."""
        httpx_mock.add_response(status_code=400, json={"message": "Content required"})

        result = runner.invoke(
            cli, ["comments", "create", "page-123", "-c", ""]
        )
        assert result.exit_code == 1


class TestCommentsUpdateCommand:
    """Tests for comments update command."""

    def test_update_comment(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Update a comment."""
        httpx_mock.add_response(json={"id": "c-1", "content": "Updated content"})

        result = runner.invoke(
            cli, ["comments", "update", "c-1", "--content", "Updated content"]
        )
        assert result.exit_code == 0
        assert "Comment updated" in result.output

    def test_update_comment_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update comment handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "Comment not found"})

        result = runner.invoke(
            cli, ["comments", "update", "nonexistent", "-c", "content"]
        )
        assert result.exit_code == 1
        assert "Comment not found" in result.output


class TestCommentsResolveCommand:
    """Tests for comments resolve command."""

    def test_resolve_comment(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Resolve a comment."""
        httpx_mock.add_response(json={"id": "c-1", "resolved": True})

        result = runner.invoke(cli, ["comments", "resolve", "c-1"])
        assert result.exit_code == 0
        assert "Comment resolved" in result.output

    def test_unresolve_comment(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Unresolve a comment."""
        httpx_mock.add_response(json={"id": "c-1", "resolved": False})

        result = runner.invoke(cli, ["comments", "resolve", "c-1", "--unresolved"])
        assert result.exit_code == 0
        assert "Comment unresolved" in result.output

    def test_resolve_with_short_flag(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Resolve with -r flag."""
        httpx_mock.add_response(json={"id": "c-1"})

        result = runner.invoke(cli, ["comments", "resolve", "c-1", "-r"])
        assert result.exit_code == 0

    def test_unresolve_with_short_flag(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Unresolve with -u flag."""
        httpx_mock.add_response(json={"id": "c-1"})

        result = runner.invoke(cli, ["comments", "resolve", "c-1", "-u"])
        assert result.exit_code == 0
        assert "Comment unresolved" in result.output


class TestCommentsDeleteCommand:
    """Tests for comments delete command."""

    def test_delete_comment_with_force(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete comment with --force flag."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["comments", "delete", "c-1", "--force"])
        assert result.exit_code == 0
        assert "Comment deleted" in result.output

    def test_delete_comment_with_confirmation(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete comment with confirmation."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["comments", "delete", "c-1"], input="y\n")
        assert result.exit_code == 0

    def test_delete_comment_cancelled(self, runner: CliRunner, mock_auth) -> None:
        """Delete comment cancelled by user."""
        result = runner.invoke(cli, ["comments", "delete", "c-1"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output

    def test_delete_comment_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete comment handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "Comment not found"})

        result = runner.invoke(cli, ["comments", "delete", "c-1", "-f"])
        assert result.exit_code == 1
        assert "Comment not found" in result.output
