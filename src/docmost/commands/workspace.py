"""Workspace commands for Docmost CLI."""

import click

from docmost.client import DocmostError, get_client
from docmost.output import error, output, success


@click.group()
def workspace() -> None:
    """Manage workspace."""
    pass


@workspace.command("info")
@click.pass_context
def workspace_info(ctx: click.Context) -> None:
    """Get workspace information."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/workspace/info", {})
        output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@workspace.command("update")
@click.option("--name", "-n", help="New workspace name")
@click.option("--description", "-d", help="New workspace description")
@click.option("--logo", help="Logo URL")
@click.pass_context
def update_workspace(
    ctx: click.Context,
    name: str | None,
    description: str | None,
    logo: str | None,
) -> None:
    """Update workspace settings."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if logo:
            data["logo"] = logo
        result = client.post("/workspace/update", data)
        output(result, ctx.obj.format)
        success("Workspace updated")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@workspace.command("members")
@click.option("--query", "-q", help="Search query")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=50, help="Items per page")
@click.pass_context
def workspace_members(ctx: click.Context, query: str | None, page: int, limit: int) -> None:
    """List workspace members."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str | int] = {"page": page, "limit": limit}
        if query:
            data["query"] = query
        result = client.post("/workspace/members", data)
        members = result.get("items", result.get("members", result))
        if isinstance(members, list):
            output(members, ctx.obj.format, columns=["id", "name", "email", "role"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@workspace.group("invites")
def invites() -> None:
    """Manage workspace invitations."""
    pass


@invites.command("list")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=50, help="Items per page")
@click.pass_context
def list_invites(ctx: click.Context, page: int, limit: int) -> None:
    """List pending invitations."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/workspace/invitations/list", {"page": page, "limit": limit})
        invitations = result.get("items", result.get("invitations", result))
        if isinstance(invitations, list):
            output(invitations, ctx.obj.format, columns=["id", "email", "role", "createdAt"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@invites.command("create")
@click.option("--emails", "-e", required=True, help="Comma-separated email addresses")
@click.option("--role", "-r", required=True, help="Role for invitees")
@click.pass_context
def create_invite(ctx: click.Context, emails: str, role: str) -> None:
    """Create workspace invitations."""
    try:
        client = get_client(url=ctx.obj.url)
        email_list = [e.strip() for e in emails.split(",")]
        result = client.post(
            "/workspace/invitations/create",
            {
                "emails": email_list,
                "role": role,
            },
        )
        output(result, ctx.obj.format)
        success(f"Invited {len(email_list)} user(s)")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@invites.command("revoke")
@click.argument("invitation_id")
@click.pass_context
def revoke_invite(ctx: click.Context, invitation_id: str) -> None:
    """Revoke a pending invitation."""
    try:
        client = get_client(url=ctx.obj.url)
        client.post("/workspace/invitations/revoke", {"invitationId": invitation_id})
        success(f"Invitation '{invitation_id}' revoked")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)
