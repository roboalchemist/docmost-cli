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
@click.option("--content", "-c", help="Page content (markdown text)")
@click.option("--content-file", help="Path to markdown/HTML file with content")
@click.option("--parent-id", "-p", help="Parent page ID")
@click.pass_context
def create_page(
    ctx: click.Context,
    space_id: str,
    title: str,
    content: str | None,
    content_file: str | None,
    parent_id: str | None,
) -> None:
    """Create a new page.

    If --content or --content-file is provided, uses the import endpoint
    to create a page with actual content. Otherwise creates an empty page.
    """
    try:
        client = get_client(url=ctx.obj.url)

        # If content is provided, use import endpoint
        if content or content_file:
            import tempfile
            import os

            # Create temp file with content
            if content:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".md", delete=False
                ) as tmp:
                    # Add title as H1 if not already present
                    if not content.strip().startswith("#"):
                        tmp.write(f"# {title}\n\n{content}")
                    else:
                        tmp.write(content)
                    tmp_path = tmp.name
            else:
                tmp_path = content_file

            try:
                result = client.upload_file("/pages/import", tmp_path, {"spaceId": space_id})
                # Update title if specified and different from extracted title
                if result.get("title") != title:
                    client.post("/pages/update", {"pageId": result["id"], "title": title})
                    result["title"] = title
                output(result, ctx.obj.format)
                success(f"Page '{title}' created with content")
            finally:
                if content and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            # No content - create empty page with metadata only
            data: dict[str, str] = {"spaceId": space_id, "title": title}
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
@click.option("--content", "-c", help="New page content (markdown text)")
@click.option("--content-file", help="Path to markdown/HTML file with new content")
@click.option("--icon", help="Page icon")
@click.option("--cover-photo", help="Cover photo URL")
@click.pass_context
def update_page(
    ctx: click.Context,
    page_id: str,
    title: str | None,
    content: str | None,
    content_file: str | None,
    icon: str | None,
    cover_photo: str | None,
) -> None:
    """Update a page.

    WARNING: Content updates require page deletion and re-import due to
    Docmost API limitations. The page will get a new ID and URL.
    Use with caution if the page is referenced elsewhere.
    """
    try:
        client = get_client(url=ctx.obj.url)

        # If content update requested, need to delete and re-import
        if content or content_file:
            # Get current page info
            page_info = client.post("/pages/info", {"pageId": page_id})
            current_title = page_info.get("title", title or "Untitled")
            space_id = page_info["spaceId"]
            parent_id = page_info.get("parentPageId")
            current_icon = page_info.get("icon")
            current_cover = page_info.get("coverPhoto")

            # Confirm with user since this changes the page ID
            if not click.confirm(
                f"⚠️  Content update requires deleting and re-importing the page.\n"
                f"The page will get a new ID and URL. Continue?",
                default=False,
            ):
                click.echo("Cancelled")
                return

            # Delete old page
            client.post("/pages/delete", {"pageId": page_id})

            # Import with new content
            import tempfile
            import os

            if content:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".md", delete=False
                ) as tmp:
                    final_title = title or current_title
                    if not content.strip().startswith("#"):
                        tmp.write(f"# {final_title}\n\n{content}")
                    else:
                        tmp.write(content)
                    tmp_path = tmp.name
            else:
                tmp_path = content_file

            try:
                result = client.upload_file("/pages/import", tmp_path, {"spaceId": space_id})

                # Update metadata if different from imported values
                update_data = {"pageId": result["id"]}
                if title and result.get("title") != title:
                    update_data["title"] = title
                if icon or current_icon:
                    update_data["icon"] = icon or current_icon
                if cover_photo or current_cover:
                    update_data["coverPhoto"] = cover_photo or current_cover

                if len(update_data) > 1:  # More than just pageId
                    result = client.post("/pages/update", update_data)

                output(result, ctx.obj.format)
                success(f"Page '{result.get('title')}' updated with new content")
                click.echo(f"⚠️  New URL: https://docmost.roboalch.com/s/{page_info.get('space', {}).get('slug', 'unknown')}/{result.get('slugId')}")
            finally:
                if content and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            # Metadata-only update
            data: dict[str, str] = {"pageId": page_id}
            if title:
                data["title"] = title
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


@pages.command("import")
@click.option("--space-id", "-s", required=True, help="Space ID")
@click.option("--file", "-f", required=True, type=click.Path(exists=True), help="Markdown or HTML file to import")
@click.option("--title", "-t", help="Page title (defaults to filename or first H1)")
@click.pass_context
def import_page(
    ctx: click.Context,
    space_id: str,
    file: str,
    title: str | None,
) -> None:
    """Import a markdown or HTML file as a page with content.

    This is the correct way to create pages with content programmatically.
    The /pages/create endpoint only supports metadata, not content.
    """
    try:
        client = get_client(url=ctx.obj.url)
        result = client.upload_file("/pages/import", file, {"spaceId": space_id})

        # Get space info for correct URL
        space_info = client.post("/spaces/info", {"spaceId": space_id})
        space_slug = space_info.get("slug", "unknown")

        output(result, ctx.obj.format)
        page_title = result.get("title", title or "Imported page")
        page_url = f"https://docmost.roboalch.com/s/{space_slug}/{result.get('slugId', '')}"
        success(f"Page '{page_title}' imported successfully")
        if ctx.obj.format == "table":
            click.echo(f"URL: {page_url}")
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


def generate_position(index: int = 0) -> str:
    """Generate a valid position string (5-12 chars) for page ordering.

    Uses a simple base62 encoding approach to generate unique positions.
    """
    import time
    import random

    # Base62 alphabet (same as fractional-indexing uses)
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    # Generate a position based on timestamp + index + random
    # This ensures unique positions that sort correctly
    ts = int(time.time() * 1000) % (62 ** 4)  # Use last ~4 chars worth of timestamp
    val = ts * 1000 + index * 10 + random.randint(0, 9)

    # Convert to base62
    result = []
    while val > 0:
        result.append(alphabet[val % 62])
        val //= 62

    # Pad to minimum 5 chars, prefix with 'a' to sort after existing
    pos = "a" + "".join(reversed(result)).zfill(5)

    # Ensure max 12 chars
    return pos[:12]


@pages.command("move")
@click.argument("page_id")
@click.option("--parent-id", "-p", help="New parent page ID (empty for root)")
@click.option("--position", help="Position string (5-12 chars, auto-generated if not specified)")
@click.option("--after", help="Place after this page ID")
@click.option("--before", help="Place before this page ID")
@click.pass_context
def move_page(
    ctx: click.Context,
    page_id: str,
    parent_id: str | None,
    position: str | None,
    after: str | None,
    before: str | None,
) -> None:
    """Move a page to a new location."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str | None] = {"pageId": page_id}

        # Position is required by the API - generate one if not provided
        if position:
            data["position"] = position
        else:
            data["position"] = generate_position()

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
        # Handle both list and dict responses
        if isinstance(result, list):
            pages_data = result
        else:
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
        # Handle both list and dict responses
        if isinstance(result, list):
            pages_data = result
        else:
            pages_data = result.get("items", result.get("pages", result))
        if isinstance(pages_data, list):
            output(pages_data, ctx.obj.format, columns=["id", "title", "spaceId", "updatedAt"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


def extract_content_from_zip(zip_data: bytes) -> str:
    """Extract markdown/HTML content from a ZIP file.

    Args:
        zip_data: Raw ZIP file bytes

    Returns:
        Extracted content as string
    """
    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zf:
        # Get the first file in the ZIP (should be the markdown/html export)
        file_list = zf.namelist()
        if not file_list:
            raise DocmostError("Export ZIP file is empty")

        # Read the first file (usually the exported content)
        content_file = file_list[0]
        return zf.read(content_file).decode("utf-8")


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

        # The export endpoint returns a ZIP file, not JSON
        raw_data = client.post_binary(
            "/pages/export", {"pageId": page_id, "format": export_format}
        )

        # Check if response is a ZIP file (starts with PK signature)
        if raw_data[:2] == b"PK":
            content = extract_content_from_zip(raw_data)
        else:
            # Fallback: if it's plain text, decode it directly
            content = raw_data.decode("utf-8")

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
        # Handle both list and dict responses
        if isinstance(result, list):
            history = result
        else:
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
        # Handle both list and dict responses
        if isinstance(result, list):
            breadcrumbs = result
        else:
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
