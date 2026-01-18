"""Comments commands for Docmost CLI."""

import click

from docmost.client import DocmostError, get_client
from docmost.output import error, output, success


@click.group()
def comments() -> None:
    """Manage comments."""
    pass


@comments.command("list")
@click.argument("page_id")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=50, help="Items per page")
@click.pass_context
def list_comments(ctx: click.Context, page_id: str, page: int, limit: int) -> None:
    """List comments on a page."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/comments/list", {"pageId": page_id, "page": page, "limit": limit})
        comments_data = result.get("items", result.get("comments", result))
        if isinstance(comments_data, list):
            output(comments_data, ctx.obj.format, columns=["id", "content", "creatorId", "resolved", "createdAt"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@comments.command("create")
@click.argument("page_id")
@click.option("--content", "-c", required=True, help="Comment content")
@click.option("--selection", "-s", help="Text selection (JSON)")
@click.option("--parent-id", "-p", help="Parent comment ID for replies")
@click.pass_context
def create_comment(
    ctx: click.Context,
    page_id: str,
    content: str,
    selection: str | None,
    parent_id: str | None,
) -> None:
    """Create a comment on a page."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {"pageId": page_id, "content": content}
        if selection:
            data["selection"] = selection
        if parent_id:
            data["parentCommentId"] = parent_id
        result = client.post("/comments/create", data)
        output(result, ctx.obj.format)
        success("Comment created")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@comments.command("update")
@click.argument("comment_id")
@click.option("--content", "-c", required=True, help="New comment content")
@click.pass_context
def update_comment(ctx: click.Context, comment_id: str, content: str) -> None:
    """Update a comment."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/comments/update", {"commentId": comment_id, "content": content})
        output(result, ctx.obj.format)
        success("Comment updated")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@comments.command("resolve")
@click.argument("comment_id")
@click.option(
    "--resolved/--unresolved", "-r/-u",
    default=True,
    help="Set resolved status (default: resolved)"
)
@click.pass_context
def resolve_comment(ctx: click.Context, comment_id: str, resolved: bool) -> None:
    """Resolve or unresolve a comment."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/comments/resolve", {
            "commentId": comment_id,
            "resolved": str(resolved).lower(),
        })
        output(result, ctx.obj.format)
        status = "resolved" if resolved else "unresolved"
        success(f"Comment {status}")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@comments.command("delete")
@click.argument("comment_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_comment(ctx: click.Context, comment_id: str, force: bool) -> None:
    """Delete a comment."""
    if not force:
        if not click.confirm(f"Are you sure you want to delete comment '{comment_id}'?"):
            click.echo("Cancelled")
            return

    try:
        client = get_client(url=ctx.obj.url)
        client.post("/comments/delete", {"commentId": comment_id})
        success("Comment deleted")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)
