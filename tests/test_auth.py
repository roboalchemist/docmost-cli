"""Tests for authentication and token management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from docmost.auth import delete_token, get_token, is_authenticated, save_token


class TestGetToken:
    """Tests for get_token."""

    def test_returns_env_token_first(self, tmp_path) -> None:
        """Environment variable DOCMOST_TOKEN takes precedence."""
        token_file = tmp_path / "token"
        token_file.write_text("file-token")
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch.dict(os.environ, {"DOCMOST_TOKEN": "env-token"}):
                assert get_token() == "env-token"

    def test_returns_file_token_when_no_env(self, tmp_path) -> None:
        """Returns token from file when env var not set."""
        token_file = tmp_path / "token"
        token_file.write_text("stored-token")
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                # Remove DOCMOST_TOKEN if it exists
                os.environ.pop("DOCMOST_TOKEN", None)
                assert get_token() == "stored-token"

    def test_strips_whitespace_from_file_token(self, tmp_path) -> None:
        """Token from file has whitespace stripped."""
        token_file = tmp_path / "token"
        token_file.write_text("  my-token  \n")
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop("DOCMOST_TOKEN", None)
                assert get_token() == "my-token"

    def test_returns_none_when_no_token(self, tmp_path) -> None:
        """Returns None when no token is available."""
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop("DOCMOST_TOKEN", None)
                assert get_token() is None


class TestSaveToken:
    """Tests for save_token."""

    def test_saves_token_to_file(self, tmp_path) -> None:
        """Saves token to the token file."""
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            save_token("new-token")
            token_file = tmp_path / "token"
            assert token_file.exists()
            assert token_file.read_text() == "new-token"

    def test_sets_secure_permissions(self, tmp_path) -> None:
        """Token file has 600 permissions."""
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            save_token("secure-token")
            token_file = tmp_path / "token"
            # Check permissions (0o600 = user read/write only)
            assert (token_file.stat().st_mode & 0o777) == 0o600

    def test_overwrites_existing_token(self, tmp_path) -> None:
        """Saving a token overwrites existing token."""
        token_file = tmp_path / "token"
        token_file.write_text("old-token")
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            save_token("new-token")
            assert token_file.read_text() == "new-token"


class TestDeleteToken:
    """Tests for delete_token."""

    def test_deletes_token_file(self, tmp_path) -> None:
        """Deletes the token file."""
        token_file = tmp_path / "token"
        token_file.write_text("my-token")
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            delete_token()
            assert not token_file.exists()

    def test_handles_missing_token_file(self, tmp_path) -> None:
        """Handles case where token file doesn't exist."""
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            # Should not raise an exception
            delete_token()


class TestIsAuthenticated:
    """Tests for is_authenticated."""

    def test_returns_true_when_token_exists(self, tmp_path) -> None:
        """Returns True when a token is available."""
        token_file = tmp_path / "token"
        token_file.write_text("valid-token")
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop("DOCMOST_TOKEN", None)
                assert is_authenticated() is True

    def test_returns_true_when_env_token_exists(self, tmp_path) -> None:
        """Returns True when env token is available."""
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch.dict(os.environ, {"DOCMOST_TOKEN": "env-token"}):
                assert is_authenticated() is True

    def test_returns_false_when_no_token(self, tmp_path) -> None:
        """Returns False when no token is available."""
        with patch("docmost.auth.get_config_dir", return_value=tmp_path):
            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop("DOCMOST_TOKEN", None)
                assert is_authenticated() is False
