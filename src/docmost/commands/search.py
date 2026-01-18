"""Search commands for Docmost CLI."""

import click

from docmost.client import DocmostError, get_client
from docmost.output import error, output


@click.command()
@click.argument("query")
@click.option("--space-id", "-s", help="Filter by space ID")
@click.option("--page", "-p", type=int, default=1, help="Page number")
@click.option("--limit", "-l", type=int, default=20, help="Items per page")
@click.pass_context
def search(ctx: click.Context, query: str, space_id: str | None, page: int, limit: int) -> None:
    """Search pages and content."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str | int] = {"query": query, "page": page, "limit": limit}
        if space_id:
            data["spaceId"] = space_id
        result = client.post("/search", data)
        # Handle both list and dict responses
        if isinstance(result, list):
            results = result
        else:
            results = result.get("items", result.get("results", result))
        if isinstance(results, list):
            output(results, ctx.obj.format, columns=["id", "title", "spaceId", "highlight"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)


@click.command("suggest")
@click.argument("query")
@click.option(
    "--include-users/--no-include-users", "-u", default=False, help="Include users in results"
)
@click.option(
    "--include-groups/--no-include-groups", "-g", default=False, help="Include groups in results"
)
@click.pass_context
def suggest(ctx: click.Context, query: str, include_users: bool, include_groups: bool) -> None:
    """Get search suggestions (autocomplete)."""
    try:
        client = get_client(url=ctx.obj.url)
        data: dict[str, str | bool] = {"query": query}
        if include_users:
            data["includeUsers"] = True
        if include_groups:
            data["includeGroups"] = True
        result = client.post("/search/suggest", data)
        # Handle both list and dict responses
        if isinstance(result, list):
            suggestions = result
        else:
            suggestions = result.get("items", result.get("suggestions", result))
        if isinstance(suggestions, list):
            output(suggestions, ctx.obj.format, columns=["id", "title", "type"])
        else:
            output(result, ctx.obj.format)
    except DocmostError as e:
        error(str(e))
        raise SystemExit(1)
