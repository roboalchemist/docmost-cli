"""Main CLI entry point for Docmost."""

import click

from docmost import __version__
from docmost.commands import auth, comments, groups, pages, search, spaces, users, workspace
from docmost.config import load_config


class Context:
    """CLI context object for passing configuration."""

    def __init__(self, url: str | None = None, fmt: str | None = None, config_file: str | None = None):
        self.config = load_config()

        # Override with CLI options
        if url:
            self.config["url"] = url
        if fmt:
            self.config["default_format"] = fmt

        self.url = self.config.get("url")
        self.format = self.config.get("default_format", "table")


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.option("--url", "-u", envvar="DOCMOST_URL", help="Docmost API URL")
@click.option(
    "--format", "-f", "fmt",
    type=click.Choice(["json", "table", "plain"]),
    help="Output format"
)
@click.option("--config", "-c", "config_file", type=click.Path(), help="Config file path")
@click.version_option(version=__version__, prog_name="docmost")
@click.pass_context
def cli(ctx: click.Context, url: str | None, fmt: str | None, config_file: str | None) -> None:
    """Docmost CLI - Interact with your Docmost instance."""
    ctx.obj = Context(url=url, fmt=fmt, config_file=config_file)


# Register command groups
cli.add_command(auth.login)
cli.add_command(auth.logout)
cli.add_command(spaces.spaces)
cli.add_command(pages.pages)
cli.add_command(users.users)
cli.add_command(workspace.workspace)
cli.add_command(groups.groups)
cli.add_command(comments.comments)
cli.add_command(search.search)
cli.add_command(search.suggest)


if __name__ == "__main__":
    cli()
