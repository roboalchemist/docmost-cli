"""Configuration management for Docmost CLI."""

import os
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path.home() / ".config" / "docmost"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
TOKEN_FILE = CONFIG_DIR / "token"


def get_config_dir() -> Path:
    """Get the configuration directory, creating it if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> dict[str, Any]:
    """Load configuration from file and environment variables.

    Environment variables take precedence over config file.
    """
    config: dict[str, Any] = {
        "url": None,
        "default_format": "table",
        "default_space": None,
    }

    # Load from config file if it exists
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            file_config = yaml.safe_load(f) or {}
            config.update(file_config)

    # Override with environment variables
    if env_url := os.environ.get("DOCMOST_URL"):
        config["url"] = env_url

    if env_format := os.environ.get("DOCMOST_FORMAT"):
        config["default_format"] = env_format

    if env_space := os.environ.get("DOCMOST_SPACE"):
        config["default_space"] = env_space

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    get_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def get_url(config: dict[str, Any] | None = None) -> str | None:
    """Get the Docmost API URL."""
    if config is None:
        config = load_config()
    return config.get("url")


def get_default_format(config: dict[str, Any] | None = None) -> str:
    """Get the default output format."""
    if config is None:
        config = load_config()
    return config.get("default_format", "table")


def get_default_space(config: dict[str, Any] | None = None) -> str | None:
    """Get the default space ID."""
    if config is None:
        config = load_config()
    return config.get("default_space")
