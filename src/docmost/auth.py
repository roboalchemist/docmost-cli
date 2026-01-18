"""Authentication and token management for Docmost CLI."""

import os

from docmost.config import get_config_dir

TOKEN_FILE = get_config_dir() / "token"


def get_token() -> str | None:
    """Get the stored access token.

    Checks environment variable first, then token file.
    """
    # Check environment variable first
    if env_token := os.environ.get("DOCMOST_TOKEN"):
        return env_token

    # Check token file
    token_file = get_config_dir() / "token"
    if token_file.exists():
        return token_file.read_text().strip()

    return None


def save_token(token: str) -> None:
    """Save access token to file with secure permissions."""
    token_file = get_config_dir() / "token"

    # Write token
    token_file.write_text(token)

    # Set permissions to user-only read/write (600)
    token_file.chmod(0o600)


def delete_token() -> None:
    """Delete the stored access token."""
    token_file = get_config_dir() / "token"
    if token_file.exists():
        token_file.unlink()


def is_authenticated() -> bool:
    """Check if there is a valid token stored."""
    return get_token() is not None
