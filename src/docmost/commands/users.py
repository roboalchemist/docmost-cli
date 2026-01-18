"""Users commands for Docmost CLI."""

import click

from docmost.client import DocmostError, get_client
from docmost.output import error, output, success


@click.group()
def users() -> None:
    """Manage users."""
    pass


@users.command("me")
@click.pass_context
def current_user(ctx: click.Context) -> None:
    """Get current user information."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/users/me", {})
        output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@users.command("update")
@click.argument("user_id")
@click.option("--name", "-n", help="New user name")
@click.option("--email", "-e", help="New email address")
@click.option("--role", "-r", help="New role")
@click.pass_context
def update_user(
    ctx: click.Context,
    user_id: str,
    name: str | None,
    email: str | None,
    role: str | None,
) -> None:
    """Update a user."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {"userId": user_id}
        if name:
            data["name"] = name
        if email:
            data["email"] = email
        if role:
            data["role"] = role
        result = client.post("/users/update", data)
        output(result, ctx.obj.format)
        success(f"User '{user_id}' updated")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)
