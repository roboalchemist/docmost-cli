"""Tests for users commands."""

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


class TestUsersMeCommand:
    """Tests for users me command."""

    def test_current_user(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get current user info."""
        httpx_mock.add_response(
            json={
                "id": "user-123",
                "name": "Test User",
                "email": "test@example.com",
                "role": "admin",
            }
        )

        result = runner.invoke(cli, ["users", "me"])
        assert result.exit_code == 0
        assert "Test User" in result.output
        assert "test@example.com" in result.output

    def test_current_user_auth_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Current user handles auth error."""
        httpx_mock.add_response(status_code=401, json={"message": "Invalid token"})

        result = runner.invoke(cli, ["users", "me"])
        assert result.exit_code == 1
        assert "Authentication failed" in result.output


class TestUsersUpdateCommand:
    """Tests for users update command."""

    def test_update_user_name(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Update user name."""
        httpx_mock.add_response(json={"id": "user-1", "name": "New Name"})

        result = runner.invoke(
            cli, ["users", "update", "user-1", "--name", "New Name"]
        )
        assert result.exit_code == 0
        assert "User 'user-1' updated" in result.output

    def test_update_user_email(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Update user email."""
        httpx_mock.add_response(json={"id": "user-1"})

        result = runner.invoke(
            cli, ["users", "update", "user-1", "-e", "newemail@example.com"]
        )
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b'"email":"newemail@example.com"' in request.content

    def test_update_user_role(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Update user role."""
        httpx_mock.add_response(json={"id": "user-1"})

        result = runner.invoke(cli, ["users", "update", "user-1", "-r", "member"])
        assert result.exit_code == 0

    def test_update_user_multiple_fields(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update multiple user fields."""
        httpx_mock.add_response(json={"id": "user-1"})

        result = runner.invoke(
            cli,
            [
                "users",
                "update",
                "user-1",
                "-n",
                "Updated User",
                "-e",
                "updated@example.com",
                "-r",
                "admin",
            ],
        )
        assert result.exit_code == 0

    def test_update_user_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update user handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "User not found"})

        result = runner.invoke(cli, ["users", "update", "nonexistent", "-n", "Name"])
        assert result.exit_code == 1
        assert "User not found" in result.output

    def test_update_user_permission_denied(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update user handles permission denied."""
        httpx_mock.add_response(status_code=403, json={"message": "Permission denied"})

        result = runner.invoke(cli, ["users", "update", "user-1", "-r", "admin"])
        assert result.exit_code == 1
        assert "Permission denied" in result.output
