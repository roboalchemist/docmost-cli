"""Groups commands for Docmost CLI."""

import click

from docmost.client import DocmostError, get_client
from docmost.output import error, output, success


@click.group()
def groups() -> None:
    """Manage groups."""
    pass


@groups.command("list")
@click.option("--query", "-q", help="Search query")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=50, help="Items per page")
@click.pass_context
def list_groups(ctx: click.Context, query: str | None, page: int, limit: int) -> None:
    """List all groups."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str | int] = {"page": page, "limit": limit}
        if query:
            data["query"] = query
        result = client.post("/groups/list", data)
        groups_data = result.get("items", result.get("groups", result))
        if isinstance(groups_data, list):
            output(
                groups_data, ctx.obj.format, columns=["id", "name", "description", "memberCount"]
            )
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@groups.command("info")
@click.argument("group_id")
@click.pass_context
def group_info(ctx: click.Context, group_id: str) -> None:
    """Get group information."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/groups/info", {"groupId": group_id})
        output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@groups.command("create")
@click.option("--name", "-n", required=True, help="Group name")
@click.option("--description", "-d", help="Group description")
@click.pass_context
def create_group(ctx: click.Context, name: str, description: str | None) -> None:
    """Create a new group."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {"name": name}
        if description:
            data["description"] = description
        result = client.post("/groups/create", data)
        output(result, ctx.obj.format)
        success(f"Group '{name}' created")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@groups.command("update")
@click.argument("group_id")
@click.option("--name", "-n", help="New group name")
@click.option("--description", "-d", help="New group description")
@click.pass_context
def update_group(
    ctx: click.Context, group_id: str, name: str | None, description: str | None
) -> None:
    """Update a group."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {"groupId": group_id}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        result = client.post("/groups/update", data)
        output(result, ctx.obj.format)
        success(f"Group '{group_id}' updated")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@groups.command("delete")
@click.argument("group_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_group(ctx: click.Context, group_id: str, force: bool) -> None:
    """Delete a group."""
    if not force:
        if not click.confirm(f"Are you sure you want to delete group '{group_id}'?"):
            click.echo("Cancelled")
            return

    try:
        client = get_client(url=ctx.obj.url)
        client.post("/groups/delete", {"groupId": group_id})
        success(f"Group '{group_id}' deleted")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@groups.command("members")
@click.argument("group_id")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=50, help="Items per page")
@click.pass_context
def group_members(ctx: click.Context, group_id: str, page: int, limit: int) -> None:
    """List group members."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/groups/members", {"groupId": group_id, "page": page, "limit": limit})
        members = result.get("items", result.get("members", result))
        if isinstance(members, list):
            output(members, ctx.obj.format, columns=["id", "name", "email"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@groups.command("members-add")
@click.argument("group_id")
@click.option("--user-ids", "-u", required=True, help="Comma-separated user IDs")
@click.pass_context
def add_members(ctx: click.Context, group_id: str, user_ids: str) -> None:
    """Add members to a group."""
    try:
        client = get_client(url=ctx.obj.url)
        ids = [uid.strip() for uid in user_ids.split(",")]
        result = client.post(
            "/groups/members/add",
            {
                "groupId": group_id,
                "userIds": ids,
            },
        )
        output(result, ctx.obj.format)
        success(f"Added {len(ids)} member(s) to group '{group_id}'")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@groups.command("members-remove")
@click.argument("group_id")
@click.option("--user-id", "-u", required=True, help="User ID to remove")
@click.pass_context
def remove_member(ctx: click.Context, group_id: str, user_id: str) -> None:
    """Remove a member from a group."""
    try:
        client = get_client(url=ctx.obj.url)
        client.post("/groups/members/remove", {"groupId": group_id, "userId": user_id})
        success(f"Removed user '{user_id}' from group '{group_id}'")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)
