"""Authentication commands for Docmost CLI."""

import click
import httpx

from docmost import auth as auth_module
from docmost.config import get_config_dir, load_config, save_config
from docmost.output import error, success


@click.command()
@click.option("--url", "-u", prompt="Docmost URL", help="Docmost instance URL (e.g., https://docs.example.com)")
@click.option("--email", "-e", prompt="Email", help="Your email address")
@click.option("--password", "-p", prompt="Password", hide_input=True, help="Your password")
def login(url: str, email: str, password: str) -> None:
    """Login to Docmost and store access token."""
    # Ensure URL has /api suffix
    api_url = url.rstrip("/")
    if not api_url.endswith("/api"):
        api_url = f"{api_url}/api"

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{api_url}/auth/login",
                data={"email": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code == 401:
                error("Invalid email or password")
                raise SystemExit(1)

            if response.status_code != 200:
                error(f"Login failed: {response.text}")
                raise SystemExit(1)

            data = response.json()
            token = data.get("token") or data.get("accessToken") or data.get("access_token")

            if not token:
                error("No token received from server")
                raise SystemExit(1)

            # Save token
            auth_module.save_token(token)

            # Save URL to config
            config = load_config()
            config["url"] = api_url
            save_config(config)

            success(f"Logged in successfully. Config saved to {get_config_dir()}")

    except httpx.RequestError as e:
        error(f"Connection error: {e}")
        raise SystemExit(1)


@click.command()
def logout() -> None:
    """Remove stored access token."""
    if auth_module.is_authenticated():
        auth_module.delete_token()
        success("Logged out successfully")
    else:
        click.echo("Not currently logged in")
