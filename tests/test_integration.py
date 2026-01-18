"""Integration tests for Docmost CLI against a live server.

These tests require:
- A running Docmost server
- Valid authentication (via docmost login or DOCMOST_TOKEN env var)
- DOCMOST_URL set in config or environment

Run with: make test-integration
"""

import json

import pytest
from click.testing import CliRunner

from docmost.auth import get_token
from docmost.cli import cli
from docmost.config import load_config


def has_live_credentials() -> bool:
    """Check if we have credentials for live server testing."""
    config = load_config()
    token = get_token()
    return config.get("url") is not None and token is not None


# Skip all tests in this module if no live credentials
pytestmark = pytest.mark.skipif(
    not has_live_credentials(),
    reason="No live server credentials (need DOCMOST_URL and token)",
)


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


class TestSpacesIntegration:
    """Integration tests for spaces commands."""

    def test_spaces_list(self, runner: CliRunner) -> None:
        """List spaces returns valid data."""
        result = runner.invoke(cli, ["spaces", "list"])
        assert result.exit_code == 0
        # Should show table output or "No results"
        assert result.output

    def test_spaces_list_json(self, runner: CliRunner) -> None:
        """List spaces with JSON output."""
        result = runner.invoke(cli, ["--format", "json", "spaces", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_spaces_info(self, runner: CliRunner) -> None:
        """Get space info for first available space."""
        # First get a space ID
        list_result = runner.invoke(cli, ["--format", "json", "spaces", "list"])
        if list_result.exit_code != 0:
            pytest.skip("Could not list spaces")

        spaces = json.loads(list_result.output)
        if not spaces:
            pytest.skip("No spaces available")

        space_id = spaces[0]["id"]
        result = runner.invoke(cli, ["spaces", "info", space_id])
        assert result.exit_code == 0
        assert space_id in result.output or spaces[0]["name"] in result.output

    def test_spaces_members(self, runner: CliRunner) -> None:
        """List space members."""
        # First get a space ID
        list_result = runner.invoke(cli, ["--format", "json", "spaces", "list"])
        if list_result.exit_code != 0:
            pytest.skip("Could not list spaces")

        spaces = json.loads(list_result.output)
        if not spaces:
            pytest.skip("No spaces available")

        space_id = spaces[0]["id"]
        result = runner.invoke(cli, ["spaces", "members", space_id])
        assert result.exit_code == 0


class TestPagesIntegration:
    """Integration tests for pages commands."""

    def test_pages_recent(self, runner: CliRunner) -> None:
        """Get recent pages."""
        result = runner.invoke(cli, ["pages", "recent"])
        assert result.exit_code == 0

    def test_pages_recent_json(self, runner: CliRunner) -> None:
        """Get recent pages with JSON output."""
        result = runner.invoke(cli, ["--format", "json", "pages", "recent"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_pages_tree(self, runner: CliRunner) -> None:
        """Get page tree for a space."""
        # First get a space ID
        list_result = runner.invoke(cli, ["--format", "json", "spaces", "list"])
        if list_result.exit_code != 0:
            pytest.skip("Could not list spaces")

        spaces = json.loads(list_result.output)
        if not spaces:
            pytest.skip("No spaces available")

        space_id = spaces[0]["id"]
        result = runner.invoke(cli, ["pages", "tree", space_id])
        assert result.exit_code == 0

    def test_pages_info(self, runner: CliRunner) -> None:
        """Get page info."""
        # First get a page ID from recent
        list_result = runner.invoke(cli, ["--format", "json", "pages", "recent"])
        if list_result.exit_code != 0:
            pytest.skip("Could not get recent pages")

        pages = json.loads(list_result.output)
        if not pages:
            pytest.skip("No pages available")

        page_id = pages[0]["id"]
        result = runner.invoke(cli, ["pages", "info", page_id])
        assert result.exit_code == 0
        assert page_id in result.output or pages[0].get("title", "") in result.output

    def test_pages_breadcrumbs(self, runner: CliRunner) -> None:
        """Get page breadcrumbs."""
        # First get a page ID
        list_result = runner.invoke(cli, ["--format", "json", "pages", "recent"])
        if list_result.exit_code != 0:
            pytest.skip("Could not get recent pages")

        pages = json.loads(list_result.output)
        if not pages:
            pytest.skip("No pages available")

        page_id = pages[0]["id"]
        result = runner.invoke(cli, ["pages", "breadcrumbs", page_id])
        assert result.exit_code == 0

    def test_pages_history(self, runner: CliRunner) -> None:
        """Get page history."""
        # First get a page ID
        list_result = runner.invoke(cli, ["--format", "json", "pages", "recent"])
        if list_result.exit_code != 0:
            pytest.skip("Could not get recent pages")

        pages = json.loads(list_result.output)
        if not pages:
            pytest.skip("No pages available")

        page_id = pages[0]["id"]
        result = runner.invoke(cli, ["pages", "history", page_id])
        assert result.exit_code == 0

    def test_pages_export_markdown(self, runner: CliRunner) -> None:
        """Export page to markdown."""
        # First get a page ID
        list_result = runner.invoke(cli, ["--format", "json", "pages", "recent"])
        if list_result.exit_code != 0:
            pytest.skip("Could not get recent pages")

        pages = json.loads(list_result.output)
        if not pages:
            pytest.skip("No pages available")

        page_id = pages[0]["id"]
        result = runner.invoke(cli, ["pages", "export", page_id, "-f", "markdown"])
        assert result.exit_code == 0


class TestWorkspaceIntegration:
    """Integration tests for workspace commands."""

    def test_workspace_info(self, runner: CliRunner) -> None:
        """Get workspace info."""
        result = runner.invoke(cli, ["workspace", "info"])
        assert result.exit_code == 0
        assert "name" in result.output.lower() or "id" in result.output.lower()

    def test_workspace_public(self, runner: CliRunner) -> None:
        """Get public workspace info."""
        result = runner.invoke(cli, ["workspace", "public"])
        assert result.exit_code == 0

    def test_workspace_members(self, runner: CliRunner) -> None:
        """List workspace members."""
        result = runner.invoke(cli, ["workspace", "members"])
        assert result.exit_code == 0

    def test_workspace_members_json(self, runner: CliRunner) -> None:
        """List workspace members with JSON output."""
        result = runner.invoke(cli, ["--format", "json", "workspace", "members"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_workspace_invites_list(self, runner: CliRunner) -> None:
        """List workspace invitations."""
        result = runner.invoke(cli, ["workspace", "invites", "list"])
        assert result.exit_code == 0


class TestGroupsIntegration:
    """Integration tests for groups commands."""

    def test_groups_list(self, runner: CliRunner) -> None:
        """List groups."""
        result = runner.invoke(cli, ["groups", "list"])
        assert result.exit_code == 0

    def test_groups_list_json(self, runner: CliRunner) -> None:
        """List groups with JSON output."""
        result = runner.invoke(cli, ["--format", "json", "groups", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_groups_info(self, runner: CliRunner) -> None:
        """Get group info."""
        # First get a group ID
        list_result = runner.invoke(cli, ["--format", "json", "groups", "list"])
        if list_result.exit_code != 0:
            pytest.skip("Could not list groups")

        groups = json.loads(list_result.output)
        if not groups:
            pytest.skip("No groups available")

        group_id = groups[0]["id"]
        result = runner.invoke(cli, ["groups", "info", group_id])
        assert result.exit_code == 0
        assert group_id in result.output or groups[0]["name"] in result.output

    def test_groups_members(self, runner: CliRunner) -> None:
        """List group members."""
        # First get a group ID
        list_result = runner.invoke(cli, ["--format", "json", "groups", "list"])
        if list_result.exit_code != 0:
            pytest.skip("Could not list groups")

        groups = json.loads(list_result.output)
        if not groups:
            pytest.skip("No groups available")

        group_id = groups[0]["id"]
        result = runner.invoke(cli, ["groups", "members", group_id])
        assert result.exit_code == 0


class TestUsersIntegration:
    """Integration tests for users commands."""

    def test_users_me(self, runner: CliRunner) -> None:
        """Get current user info."""
        result = runner.invoke(cli, ["users", "me"])
        assert result.exit_code == 0
        assert "user" in result.output.lower() or "email" in result.output.lower()

    def test_users_me_json(self, runner: CliRunner) -> None:
        """Get current user info with JSON output."""
        result = runner.invoke(cli, ["--format", "json", "users", "me"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert "user" in data or "email" in data


class TestCommentsIntegration:
    """Integration tests for comments commands."""

    def test_comments_list(self, runner: CliRunner) -> None:
        """List comments on a page."""
        # First get a page ID
        list_result = runner.invoke(cli, ["--format", "json", "pages", "recent"])
        if list_result.exit_code != 0:
            pytest.skip("Could not get recent pages")

        pages = json.loads(list_result.output)
        if not pages:
            pytest.skip("No pages available")

        page_id = pages[0]["id"]
        result = runner.invoke(cli, ["comments", "list", page_id])
        assert result.exit_code == 0


class TestSearchIntegration:
    """Integration tests for search commands."""

    def test_search(self, runner: CliRunner) -> None:
        """Search for content."""
        result = runner.invoke(cli, ["search", "test"])
        assert result.exit_code == 0

    def test_search_json(self, runner: CliRunner) -> None:
        """Search with JSON output."""
        result = runner.invoke(cli, ["--format", "json", "search", "test"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_suggest(self, runner: CliRunner) -> None:
        """Get suggestions."""
        result = runner.invoke(cli, ["suggest", "test"])
        assert result.exit_code == 0

    def test_suggest_json(self, runner: CliRunner) -> None:
        """Get suggestions with JSON output."""
        result = runner.invoke(cli, ["--format", "json", "suggest", "test"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
