"""Smoke tests for Docmost CLI."""

import pytest
from click.testing import CliRunner

from docmost import __version__
from docmost.cli import cli


class TestCliBasics:
    """Test basic CLI functionality."""

    def test_cli_loads(self, cli_runner: CliRunner) -> None:
        """Verify the CLI loads without errors."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Docmost CLI" in result.output

    def test_cli_version(self, cli_runner: CliRunner) -> None:
        """Verify --version flag works."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output

    def test_cli_has_expected_commands(self, cli_runner: CliRunner) -> None:
        """Verify expected commands are registered."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0

        expected_commands = [
            "login",
            "logout",
            "spaces",
            "pages",
            "users",
            "workspace",
            "groups",
            "comments",
            "search",
            "suggest",
        ]
        for cmd in expected_commands:
            assert cmd in result.output, f"Expected command '{cmd}' not found in CLI help"

    def test_cli_format_option(self, cli_runner: CliRunner) -> None:
        """Verify --format option is available."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--format" in result.output or "-f" in result.output

    def test_cli_url_option(self, cli_runner: CliRunner) -> None:
        """Verify --url option is available."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--url" in result.output or "-u" in result.output


class TestSubcommandHelp:
    """Test that subcommands provide help."""

    @pytest.mark.parametrize(
        "subcommand",
        ["spaces", "pages", "users", "workspace", "groups", "comments"],
    )
    def test_subcommand_help(self, cli_runner: CliRunner, subcommand: str) -> None:
        """Verify subcommands show help without errors."""
        result = cli_runner.invoke(cli, [subcommand, "--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output or "Options:" in result.output
