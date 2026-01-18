"""Tests for authentication commands."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from click.testing import CliRunner

from docmost.cli import cli
from docmost.commands.auth import login, logout


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


class TestLoginCommand:
    """Tests for the login command."""

    def test_login_success(self, runner: CliRunner, httpx_mock, tmp_path) -> None:
        """Successful login stores token and config."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            json={"token": "test-token-123"},
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.config.CONFIG_FILE", config_dir / "config.yaml"):
                with patch("docmost.auth.get_config_dir", return_value=config_dir):
                    config_dir.mkdir(parents=True, exist_ok=True)
                    result = runner.invoke(
                        cli,
                        ["login"],
                        input="https://docs.example.com\nuser@example.com\npassword123\n",
                    )

        assert result.exit_code == 0
        assert "Logged in successfully" in result.output

    def test_login_with_explicit_args(
        self, runner: CliRunner, httpx_mock, tmp_path
    ) -> None:
        """Login with command-line arguments."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            json={"accessToken": "explicit-token"},
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.config.CONFIG_FILE", config_dir / "config.yaml"):
                with patch("docmost.auth.get_config_dir", return_value=config_dir):
                    config_dir.mkdir(parents=True, exist_ok=True)
                    result = runner.invoke(
                        cli,
                        [
                            "login",
                            "--url",
                            "https://docs.example.com",
                            "--email",
                            "user@example.com",
                            "--password",
                            "pass",
                        ],
                    )

        assert result.exit_code == 0

    def test_login_adds_api_suffix(
        self, runner: CliRunner, httpx_mock, tmp_path
    ) -> None:
        """Login adds /api suffix if not present."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            json={"token": "token"},
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.config.CONFIG_FILE", config_dir / "config.yaml"):
                with patch("docmost.auth.get_config_dir", return_value=config_dir):
                    config_dir.mkdir(parents=True, exist_ok=True)
                    result = runner.invoke(
                        cli,
                        ["login", "-u", "https://docs.example.com", "-e", "u@e.com", "-p", "p"],
                    )

        assert result.exit_code == 0

    def test_login_invalid_credentials(
        self, runner: CliRunner, httpx_mock, tmp_path
    ) -> None:
        """Login fails with invalid credentials."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            status_code=401,
            json={"error": "Invalid credentials"},
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.auth.get_config_dir", return_value=config_dir):
                config_dir.mkdir(parents=True, exist_ok=True)
                result = runner.invoke(
                    cli,
                    ["login", "-u", "https://docs.example.com", "-e", "u@e.com", "-p", "p"],
                )

        assert result.exit_code == 1
        assert "Invalid email or password" in result.output

    def test_login_server_error(self, runner: CliRunner, httpx_mock, tmp_path) -> None:
        """Login fails on server error."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            status_code=500,
            text="Internal Server Error",
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.auth.get_config_dir", return_value=config_dir):
                config_dir.mkdir(parents=True, exist_ok=True)
                result = runner.invoke(
                    cli,
                    ["login", "-u", "https://docs.example.com", "-e", "u@e.com", "-p", "p"],
                )

        assert result.exit_code == 1
        assert "Login failed" in result.output

    def test_login_no_token_in_response(
        self, runner: CliRunner, httpx_mock, tmp_path
    ) -> None:
        """Login fails when no token in response."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            json={"message": "success but no token"},
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.auth.get_config_dir", return_value=config_dir):
                config_dir.mkdir(parents=True, exist_ok=True)
                result = runner.invoke(
                    cli,
                    ["login", "-u", "https://docs.example.com", "-e", "u@e.com", "-p", "p"],
                )

        assert result.exit_code == 1
        assert "No token received" in result.output

    def test_login_connection_error(self, runner: CliRunner, tmp_path) -> None:
        """Login fails on connection error."""
        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.auth.get_config_dir", return_value=config_dir):
                config_dir.mkdir(parents=True, exist_ok=True)
                with patch("httpx.Client") as mock_client:
                    mock_client.return_value.__enter__.return_value.post.side_effect = (
                        httpx.RequestError("Connection refused")
                    )
                    result = runner.invoke(
                        cli,
                        ["login", "-u", "https://docs.example.com", "-e", "u@e.com", "-p", "p"],
                    )

        assert result.exit_code == 1
        assert "Connection error" in result.output

    def test_login_handles_access_token_key(
        self, runner: CliRunner, httpx_mock, tmp_path
    ) -> None:
        """Login accepts 'access_token' key in response."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            json={"access_token": "snake-case-token"},
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.config.CONFIG_FILE", config_dir / "config.yaml"):
                with patch("docmost.auth.get_config_dir", return_value=config_dir):
                    config_dir.mkdir(parents=True, exist_ok=True)
                    result = runner.invoke(
                        cli,
                        ["login", "-u", "https://docs.example.com", "-e", "u@e.com", "-p", "p"],
                    )

        assert result.exit_code == 0

    def test_login_extracts_token_from_cookie(
        self, runner: CliRunner, httpx_mock, tmp_path
    ) -> None:
        """Login extracts authToken from Set-Cookie header (live server behavior)."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            json={"success": True, "status": 200},
            headers={"Set-Cookie": "authToken=jwt-token-from-cookie; Path=/; HttpOnly"},
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.config.CONFIG_FILE", config_dir / "config.yaml"):
                with patch("docmost.auth.get_config_dir", return_value=config_dir):
                    config_dir.mkdir(parents=True, exist_ok=True)
                    result = runner.invoke(
                        cli,
                        ["login", "-u", "https://docs.example.com", "-e", "u@e.com", "-p", "p"],
                    )

        assert result.exit_code == 0
        assert "Logged in successfully" in result.output
        # Verify token was saved
        token_file = config_dir / "token"
        assert token_file.exists()
        assert token_file.read_text() == "jwt-token-from-cookie"

    def test_login_extracts_token_from_nested_response(
        self, runner: CliRunner, httpx_mock, tmp_path
    ) -> None:
        """Login extracts token from data.tokens.accessToken (Postman spec format)."""
        httpx_mock.add_response(
            url="https://docs.example.com/api/auth/login",
            json={
                "data": {
                    "tokens": {
                        "accessToken": "nested-jwt-token"
                    }
                },
                "success": True,
                "status": 200
            },
        )

        config_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.config.CONFIG_FILE", config_dir / "config.yaml"):
                with patch("docmost.auth.get_config_dir", return_value=config_dir):
                    config_dir.mkdir(parents=True, exist_ok=True)
                    result = runner.invoke(
                        cli,
                        ["login", "-u", "https://docs.example.com", "-e", "u@e.com", "-p", "p"],
                    )

        assert result.exit_code == 0
        assert "Logged in successfully" in result.output


class TestLogoutCommand:
    """Tests for the logout command."""

    def test_logout_when_authenticated(self, runner: CliRunner, tmp_path) -> None:
        """Logout deletes token when authenticated."""
        token_file = tmp_path / "token"
        token_file.write_text("existing-token")

        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch("docmost.commands.auth.auth_module.is_authenticated", return_value=True):
                with patch("docmost.commands.auth.auth_module.delete_token") as mock_delete:
                    result = runner.invoke(cli, ["logout"])

        assert result.exit_code == 0
        assert "Logged out successfully" in result.output
        mock_delete.assert_called_once()

    def test_logout_when_not_authenticated(self, runner: CliRunner, tmp_path) -> None:
        """Logout shows message when not authenticated."""
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch("docmost.commands.auth.auth_module.is_authenticated", return_value=False):
                result = runner.invoke(cli, ["logout"])

        assert result.exit_code == 0
        assert "Not currently logged in" in result.output
