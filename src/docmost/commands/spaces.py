"""Spaces commands for Docmost CLI."""

import click

from docmost.client import DocmostError, get_client
from docmost.output import error, output, success


@click.group()
def spaces() -> None:
    """Manage spaces."""
    pass


@spaces.command("list")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=50, help="Items per page")
@click.pass_context
def list_spaces(ctx: click.Context, page: int, limit: int) -> None:
    """List all spaces."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/spaces", {"page": page, "limit": limit})
        spaces_data = result.get("items", result.get("spaces", result))
        if isinstance(spaces_data, list):
            output(spaces_data, ctx.obj.format, columns=["id", "name", "slug", "description"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@spaces.command("info")
@click.argument("space_id")
@click.pass_context
def space_info(ctx: click.Context, space_id: str) -> None:
    """Get space information."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/spaces/info", {"spaceId": space_id})
        output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@spaces.command("create")
@click.option("--name", "-n", required=True, help="Space name")
@click.option("--slug", "-s", required=True, help="Space slug (URL identifier)")
@click.option("--description", "-d", help="Space description")
@click.pass_context
def create_space(ctx: click.Context, name: str, slug: str, description: str | None) -> None:
    """Create a new space."""
    try:
        client = get_client(url=ctx.obj.url)
        data = {"name": name, "slug": slug}
        if description:
            data["description"] = description
        result = client.post("/spaces/create", data)
        output(result, ctx.obj.format)
        success(f"Space '{name}' created")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@spaces.command("update")
@click.argument("space_id")
@click.option("--name", "-n", help="New space name")
@click.option("--description", "-d", help="New space description")
@click.option("--icon", help="Space icon")
@click.pass_context
def update_space(
    ctx: click.Context, space_id: str, name: str | None, description: str | None, icon: str | None
) -> None:
    """Update a space."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {"spaceId": space_id}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if icon:
            data["icon"] = icon
        result = client.post("/spaces/update", data)
        output(result, ctx.obj.format)
        success(f"Space '{space_id}' updated")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@spaces.command("delete")
@click.argument("space_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_space(ctx: click.Context, space_id: str, force: bool) -> None:
    """Delete a space."""
    if not force:
        if not click.confirm(f"Are you sure you want to delete space '{space_id}'?"):
            click.echo("Cancelled")
            return

    try:
        client = get_client(url=ctx.obj.url)
        client.post("/spaces/delete", {"spaceId": space_id})
        success(f"Space '{space_id}' deleted")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@spaces.command("members")
@click.argument("space_id")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=50, help="Items per page")
@click.pass_context
def space_members(ctx: click.Context, space_id: str, page: int, limit: int) -> None:
    """List space members."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/spaces/members", {"spaceId": space_id, "page": page, "limit": limit})
        members = result.get("items", result.get("members", result))
        if isinstance(members, list):
            output(members, ctx.obj.format, columns=["id", "name", "email", "role"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@spaces.command("members-add")
@click.argument("space_id")
@click.option("--user-ids", "-u", required=True, help="Comma-separated user IDs")
@click.option("--role", "-r", default="member", help="Role for users (default: member)")
@click.pass_context
def add_members(ctx: click.Context, space_id: str, user_ids: str, role: str) -> None:
    """Add members to a space."""
    try:
        client = get_client(url=ctx.obj.url)
        ids = [uid.strip() for uid in user_ids.split(",")]
        result = client.post(
            "/spaces/members/add",
            {
                "spaceId": space_id,
                "userIds": ids,
                "role": role,
            },
        )
        output(result, ctx.obj.format)
        success(f"Added {len(ids)} member(s) to space '{space_id}'")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@spaces.command("members-remove")
@click.argument("space_id")
@click.option("--user-id", "-u", required=True, help="User ID to remove")
@click.pass_context
def remove_member(ctx: click.Context, space_id: str, user_id: str) -> None:
    """Remove a member from a space."""
    try:
        client = get_client(url=ctx.obj.url)
        client.post("/spaces/members/remove", {"spaceId": space_id, "userId": user_id})
        success(f"Removed user '{user_id}' from space '{space_id}'")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@spaces.command("members-change-role")
@click.argument("space_id")
@click.option("--user-id", "-u", help="User ID to change role for")
@click.option("--group-id", "-g", help="Group ID to change role for")
@click.option("--role", "-r", required=True, help="New role")
@click.pass_context
def change_member_role(
    ctx: click.Context, space_id: str, user_id: str | None, group_id: str | None, role: str
) -> None:
    """Change a member's role in a space."""
    if not user_id and not group_id:
        error("Either --user-id or --group-id must be provided")
        raise SystemExit(1)

    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {"spaceId": space_id, "role": role}
        if user_id:
            data["userId"] = user_id
        if group_id:
            data["groupId"] = group_id
        result = client.post("/spaces/members/change-role", data)
        output(result, ctx.obj.format)
        target = f"user '{user_id}'" if user_id else f"group '{group_id}'"
        success(f"Changed role for {target} in space '{space_id}' to '{role}'")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)
