"""Pages commands for Docmost CLI."""

import click

from docmost.client import DocmostError, get_client
from docmost.output import error, output, success


@click.group()
def pages() -> None:
    """Manage pages."""
    pass


@pages.command("create")
@click.option("--space-id", "-s", required=True, help="Space ID")
@click.option("--title", "-t", required=True, help="Page title")
@click.option("--content", "-c", help="Page content (JSON or markdown)")
@click.option("--parent-id", "-p", help="Parent page ID")
@click.pass_context
def create_page(
    ctx: click.Context,
    space_id: str,
    title: str,
    content: str | None,
    parent_id: str | None,
) -> None:
    """Create a new page."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {"spaceId": space_id, "title": title}
        if content:
            data["content"] = content
        if parent_id:
            data["parentPageId"] = parent_id
        result = client.post("/pages/create", data)
        output(result, ctx.obj.format)
        success(f"Page '{title}' created")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("info")
@click.argument("page_id")
@click.pass_context
def page_info(ctx: click.Context, page_id: str) -> None:
    """Get page information."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/pages/info", {"pageId": page_id})
        output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("update")
@click.argument("page_id")
@click.option("--title", "-t", help="New page title")
@click.option("--content", "-c", help="New page content")
@click.option("--icon", help="Page icon")
@click.option("--cover-photo", help="Cover photo URL")
@click.pass_context
def update_page(
    ctx: click.Context,
    page_id: str,
    title: str | None,
    content: str | None,
    icon: str | None,
    cover_photo: str | None,
) -> None:
    """Update a page."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str] = {"pageId": page_id}
        if title:
            data["title"] = title
        if content:
            data["content"] = content
        if icon:
            data["icon"] = icon
        if cover_photo:
            data["coverPhoto"] = cover_photo
        result = client.post("/pages/update", data)
        output(result, ctx.obj.format)
        success(f"Page '{page_id}' updated")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("delete")
@click.argument("page_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_page(ctx: click.Context, page_id: str, force: bool) -> None:
    """Delete a page."""
    if not force:
        if not click.confirm(f"Are you sure you want to delete page '{page_id}'?"):
            click.echo("Cancelled")
            return

    try:
        client = get_client(url=ctx.obj.url)
        client.post("/pages/delete", {"pageId": page_id})
        success(f"Page '{page_id}' deleted")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("move")
@click.argument("page_id")
@click.option("--parent-id", "-p", help="New parent page ID (empty for root)")
@click.option("--after", help="Place after this page ID")
@click.option("--before", help="Place before this page ID")
@click.pass_context
def move_page(
    ctx: click.Context,
    page_id: str,
    parent_id: str | None,
    after: str | None,
    before: str | None,
) -> None:
    """Move a page to a new location."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str | None] = {"pageId": page_id}
        if parent_id is not None:
            data["parentPageId"] = parent_id if parent_id else None
        if after:
            data["afterPageId"] = after
        if before:
            data["beforePageId"] = before
        result = client.post("/pages/move", data)
        output(result, ctx.obj.format)
        success(f"Page '{page_id}' moved")
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("tree")
@click.argument("space_id")
@click.pass_context
def page_tree(ctx: click.Context, space_id: str) -> None:
    """Get the page tree (sidebar pages) for a space."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/pages/sidebar-pages", {"spaceId": space_id})
        pages_data = result.get("items", result.get("pages", result))
        if isinstance(pages_data, list):
            output(pages_data, ctx.obj.format, columns=["id", "title", "icon", "parentPageId"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("recent")
@click.option("--space-id", "-s", help="Filter by space ID")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=20, help="Items per page")
@click.pass_context
def recent_pages(ctx: click.Context, space_id: str | None, page: int, limit: int) -> None:
    """Get recently updated pages."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str | int] = {"page": page, "limit": limit}
        if space_id:
            data["spaceId"] = space_id
        result = client.post("/pages/recent", data)
        pages_data = result.get("items", result.get("pages", result))
        if isinstance(pages_data, list):
            output(pages_data, ctx.obj.format, columns=["id", "title", "spaceId", "updatedAt"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("export")
@click.argument("page_id")
@click.option(
    "--format",
    "-f",
    "export_format",
    type=click.Choice(["html", "markdown"]),
    default="markdown",
    help="Export format",
)
@click.option("--output", "-o", "output_path", type=click.Path(), help="Output file path")
@click.pass_context
def export_page(
    ctx: click.Context, page_id: str, export_format: str, output_path: str | None
) -> None:
    """Export a page to HTML or Markdown."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/pages/export", {"pageId": page_id, "format": export_format})

        content = result.get("content", result.get("data", str(result)))

        if output_path:
            with open(output_path, "w") as f:
                f.write(content)
            success(f"Exported to {output_path}")
        else:
            click.echo(content)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("history")
@click.argument("page_id")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=20, help="Items per page")
@click.pass_context
def page_history(ctx: click.Context, page_id: str, page: int, limit: int) -> None:
    """Get page revision history."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/pages/history", {"pageId": page_id, "page": page, "limit": limit})
        history = result.get("items", result.get("history", result))
        if isinstance(history, list):
            output(history, ctx.obj.format, columns=["id", "version", "createdAt", "creatorId"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("breadcrumbs")
@click.argument("page_id")
@click.pass_context
def page_breadcrumbs(ctx: click.Context, page_id: str) -> None:
    """Get breadcrumb path for a page."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/pages/breadcrumbs", {"pageId": page_id})
        breadcrumbs = result.get("items", result.get("breadcrumbs", result))
        if isinstance(breadcrumbs, list):
            output(breadcrumbs, ctx.obj.format, columns=["id", "title", "icon"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@pages.command("history-info")
@click.argument("history_id")
@click.pass_context
def history_info(ctx: click.Context, history_id: str) -> None:
    """Get details of a specific history entry."""
    try:
        client = get_client(url=ctx.obj.url)
        result = client.post("/pages/history/info", {"historyId": history_id})
        output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)
