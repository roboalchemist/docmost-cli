"""Output formatters for Docmost CLI."""

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table

console = Console()
error_console = Console(stderr=True)


def format_json(data: Any) -> str:
    """Format data as JSON."""
    return json.dumps(data, indent=2, default=str)


def format_plain(data: dict[str, Any]) -> str:
    """Format a single item as plain key: value pairs."""
    lines = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, default=str)
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def format_table(data: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    """Format data as a rich table.

    Args:
        data: List of dictionaries to display
        columns: Optional list of columns to show. If None, uses all keys from first item.
    """
    if not data:
        console.print("[dim]No results[/dim]")
        return

    # Determine columns
    if columns is None:
        columns = list(data[0].keys())

    # Create table
    table = Table(show_header=True, header_style="bold")
    for col in columns:
        table.add_column(col)

    # Add rows
    for item in data:
        row = []
        for col in columns:
            value = item.get(col, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, default=str)
            elif value is None:
                value = ""
            else:
                value = str(value)
            row.append(value)
        table.add_row(*row)

    console.print(table)


def output(data: Any, fmt: str = "table", columns: list[str] | None = None) -> None:
    """Output data in the specified format.

    Args:
        data: Data to output
        fmt: Format - "json", "table", or "plain"
        columns: Optional columns for table format
    """
    if fmt == "json":
        click.echo(format_json(data))
    elif fmt == "plain":
        if isinstance(data, list):
            for item in data:
                click.echo(format_plain(item))
                click.echo()
        else:
            click.echo(format_plain(data))
    elif fmt == "table":
        if isinstance(data, list):
            format_table(data, columns)
        else:
            # Single item - display as plain
            click.echo(format_plain(data))
    else:
        # Default to JSON
        click.echo(format_json(data))


def success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def error(message: str) -> None:
    """Print an error message."""
    error_console.print(f"[red]✗[/red] {message}")


def warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]![/yellow] {message}")


def info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")
