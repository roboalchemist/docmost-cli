"""Tests for configuration management."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from docmost.config import (
    CONFIG_DIR,
    CONFIG_FILE,
    get_config_dir,
    get_default_format,
    get_default_space,
    get_url,
    load_config,
    save_config,
)


class TestGetConfigDir:
    """Tests for get_config_dir."""

    def test_returns_config_dir_path(self) -> None:
        """Returns the correct config directory path."""
        result = get_config_dir()
        assert result == CONFIG_DIR
        assert result == Path.home() / ".config" / "docmost"

    def test_creates_directory_if_missing(self, tmp_path) -> None:
        """Creates the config directory if it doesn't exist."""
        test_dir = tmp_path / ".config" / "docmost"
        with patch("docmost.config.CONFIG_DIR", test_dir):
            result = get_config_dir()
            # Directory should be created
            assert test_dir.exists()
            assert result.exists()


class TestLoadConfig:
    """Tests for load_config."""

    def test_returns_default_config_when_no_file(self, tmp_path) -> None:
        """Returns default config when no config file exists."""
        config_file = tmp_path / "config.yaml"
        with patch("docmost.config.CONFIG_FILE", config_file):
            config = load_config()
            assert config["url"] is None
            assert config["default_format"] == "table"
            assert config["default_space"] is None

    def test_loads_config_from_file(self, tmp_path) -> None:
        """Loads configuration from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """url: https://docs.example.com/api
default_format: json
default_space: space-123
"""
        )
        with patch("docmost.config.CONFIG_FILE", config_file):
            config = load_config()
            assert config["url"] == "https://docs.example.com/api"
            assert config["default_format"] == "json"
            assert config["default_space"] == "space-123"

    def test_env_overrides_file_url(self, tmp_path) -> None:
        """Environment variable DOCMOST_URL overrides config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("url: https://file.com/api\n")
        with patch("docmost.config.CONFIG_FILE", config_file):
            with patch.dict(os.environ, {"DOCMOST_URL": "https://env.com/api"}):
                config = load_config()
                assert config["url"] == "https://env.com/api"

    def test_env_overrides_file_format(self, tmp_path) -> None:
        """Environment variable DOCMOST_FORMAT overrides config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_format: table\n")
        with patch("docmost.config.CONFIG_FILE", config_file):
            with patch.dict(os.environ, {"DOCMOST_FORMAT": "json"}):
                config = load_config()
                assert config["default_format"] == "json"

    def test_env_overrides_file_space(self, tmp_path) -> None:
        """Environment variable DOCMOST_SPACE overrides config file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_space: file-space\n")
        with patch("docmost.config.CONFIG_FILE", config_file):
            with patch.dict(os.environ, {"DOCMOST_SPACE": "env-space"}):
                config = load_config()
                assert config["default_space"] == "env-space"

    def test_handles_empty_config_file(self, tmp_path) -> None:
        """Handles empty config file gracefully."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        with patch("docmost.config.CONFIG_FILE", config_file):
            config = load_config()
            assert config["url"] is None
            assert config["default_format"] == "table"


class TestSaveConfig:
    """Tests for save_config."""

    def test_saves_config_to_file(self, tmp_path) -> None:
        """Saves configuration to YAML file."""
        config_dir = tmp_path / ".config" / "docmost"
        config_file = config_dir / "config.yaml"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.config.CONFIG_FILE", config_file):
                save_config(
                    {
                        "url": "https://test.com/api",
                        "default_format": "plain",
                    }
                )

                assert config_file.exists()
                content = config_file.read_text()
                assert "https://test.com/api" in content
                assert "plain" in content

    def test_creates_config_dir_if_missing(self, tmp_path) -> None:
        """Creates config directory if it doesn't exist."""
        config_dir = tmp_path / "new_dir" / "docmost"
        config_file = config_dir / "config.yaml"
        with patch("docmost.config.CONFIG_DIR", config_dir):
            with patch("docmost.config.CONFIG_FILE", config_file):
                save_config({"url": "https://test.com"})
                assert config_dir.exists()


class TestGetUrl:
    """Tests for get_url helper."""

    def test_returns_url_from_provided_config(self) -> None:
        """Returns URL from provided config dict."""
        config = {"url": "https://provided.com/api"}
        assert get_url(config) == "https://provided.com/api"

    def test_loads_config_when_not_provided(self, tmp_path) -> None:
        """Loads config and returns URL when config not provided."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("url: https://loaded.com/api\n")
        with patch("docmost.config.CONFIG_FILE", config_file):
            assert get_url() == "https://loaded.com/api"

    def test_returns_none_when_url_not_set(self, tmp_path) -> None:
        """Returns None when URL is not configured."""
        config_file = tmp_path / "nonexistent.yaml"
        with patch("docmost.config.CONFIG_FILE", config_file):
            assert get_url() is None


class TestGetDefaultFormat:
    """Tests for get_default_format helper."""

    def test_returns_format_from_provided_config(self) -> None:
        """Returns format from provided config dict."""
        config = {"default_format": "json"}
        assert get_default_format(config) == "json"

    def test_returns_table_as_default(self, tmp_path) -> None:
        """Returns 'table' as default when not configured."""
        config_file = tmp_path / "nonexistent.yaml"
        with patch("docmost.config.CONFIG_FILE", config_file):
            assert get_default_format() == "table"

    def test_returns_table_when_key_missing(self) -> None:
        """Returns 'table' when key is missing from config."""
        config = {"url": "https://test.com"}
        assert get_default_format(config) == "table"


class TestGetDefaultSpace:
    """Tests for get_default_space helper."""

    def test_returns_space_from_provided_config(self) -> None:
        """Returns space from provided config dict."""
        config = {"default_space": "space-456"}
        assert get_default_space(config) == "space-456"

    def test_returns_none_when_not_set(self, tmp_path) -> None:
        """Returns None when space is not configured."""
        config_file = tmp_path / "nonexistent.yaml"
        with patch("docmost.config.CONFIG_FILE", config_file):
            assert get_default_space() is None

    def test_loads_config_when_not_provided(self, tmp_path) -> None:
        """Loads config and returns space when config not provided."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("default_space: loaded-space\n")
        with patch("docmost.config.CONFIG_FILE", config_file):
            assert get_default_space() == "loaded-space"
