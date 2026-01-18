"""Tests for spaces commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from docmost.cli import cli
from docmost.client import DocmostError


@pytest.fixture
def runner() -> CliRunner:
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_auth(tmp_path):
    """Mock authentication for tests."""
    config = {"url": "https://docs.example.com/api", "default_format": "json"}
    with patch("docmost.config.load_config", return_value=config):
        with patch("docmost.auth.get_token", return_value="test-token"):
            yield


class TestSpacesListCommand:
    """Tests for spaces list command."""

    def test_list_spaces(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """List spaces returns space data."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "space-1", "name": "Engineering", "slug": "eng"},
                    {"id": "space-2", "name": "Marketing", "slug": "mkt"},
                ]
            }
        )

        result = runner.invoke(cli, ["spaces", "list"])
        assert result.exit_code == 0
        assert "space-1" in result.output
        assert "Engineering" in result.output

    def test_list_spaces_with_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List spaces with page and limit options."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["spaces", "list", "--page", "2", "--limit", "10"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b'"page":2' in request.content
        assert b'"limit":10' in request.content

    def test_list_spaces_handles_spaces_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List handles response with 'spaces' key."""
        httpx_mock.add_response(
            json={"spaces": [{"id": "s1", "name": "Space One", "slug": "s1"}]}
        )

        result = runner.invoke(cli, ["spaces", "list"])
        assert result.exit_code == 0
        assert "Space One" in result.output

    def test_list_spaces_error(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """List handles API error."""
        httpx_mock.add_response(status_code=500, json={"message": "Server error"})

        result = runner.invoke(cli, ["spaces", "list"])
        assert result.exit_code == 1
        assert "Server error" in result.output


class TestSpacesInfoCommand:
    """Tests for spaces info command."""

    def test_space_info(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get space info."""
        httpx_mock.add_response(
            json={"id": "space-123", "name": "My Space", "description": "Test"}
        )

        result = runner.invoke(cli, ["spaces", "info", "space-123"])
        assert result.exit_code == 0
        assert "My Space" in result.output

    def test_space_info_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Space info handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "Space not found"})

        result = runner.invoke(cli, ["spaces", "info", "nonexistent"])
        assert result.exit_code == 1
        assert "Space not found" in result.output


class TestSpacesCreateCommand:
    """Tests for spaces create command."""

    def test_create_space(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Create a new space."""
        httpx_mock.add_response(json={"id": "new-space", "name": "New Space"})

        result = runner.invoke(
            cli, ["spaces", "create", "--name", "New Space", "--slug", "new-space"]
        )
        assert result.exit_code == 0
        assert "Space 'New Space' created" in result.output

    def test_create_space_with_description(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create space with description."""
        httpx_mock.add_response(json={"id": "s1", "name": "S1"})

        result = runner.invoke(
            cli,
            [
                "spaces",
                "create",
                "-n",
                "S1",
                "-s",
                "s1",
                "-d",
                "A test space",
            ],
        )
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b'"description":"A test space"' in request.content

    def test_create_space_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create space handles error."""
        httpx_mock.add_response(status_code=400, json={"message": "Slug already exists"})

        result = runner.invoke(
            cli, ["spaces", "create", "-n", "Test", "-s", "existing"]
        )
        assert result.exit_code == 1
        assert "Slug already exists" in result.output


class TestSpacesUpdateCommand:
    """Tests for spaces update command."""

    def test_update_space_name(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Update space name."""
        httpx_mock.add_response(json={"id": "space-1", "name": "Updated Name"})

        result = runner.invoke(
            cli, ["spaces", "update", "space-1", "--name", "Updated Name"]
        )
        assert result.exit_code == 0
        assert "Space 'space-1' updated" in result.output

    def test_update_space_description(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update space description."""
        httpx_mock.add_response(json={"id": "space-1"})

        result = runner.invoke(
            cli, ["spaces", "update", "space-1", "-d", "New description"]
        )
        assert result.exit_code == 0

    def test_update_space_icon(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Update space icon."""
        httpx_mock.add_response(json={"id": "space-1"})

        result = runner.invoke(cli, ["spaces", "update", "space-1", "--icon", "rocket"])
        assert result.exit_code == 0


class TestSpacesDeleteCommand:
    """Tests for spaces delete command."""

    def test_delete_space_with_force(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete space with --force flag."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["spaces", "delete", "space-1", "--force"])
        assert result.exit_code == 0
        assert "Space 'space-1' deleted" in result.output

    def test_delete_space_with_confirmation(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete space with confirmation prompt."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["spaces", "delete", "space-1"], input="y\n")
        assert result.exit_code == 0
        assert "Space 'space-1' deleted" in result.output

    def test_delete_space_cancelled(
        self, runner: CliRunner, mock_auth
    ) -> None:
        """Delete space cancelled by user."""
        result = runner.invoke(cli, ["spaces", "delete", "space-1"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output


class TestSpacesMembersCommand:
    """Tests for spaces members command."""

    def test_list_space_members(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List space members."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "user-1", "name": "Alice", "email": "alice@example.com"},
                    {"id": "user-2", "name": "Bob", "email": "bob@example.com"},
                ]
            }
        )

        result = runner.invoke(cli, ["spaces", "members", "space-1"])
        assert result.exit_code == 0
        assert "Alice" in result.output

    def test_list_space_members_with_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List members with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(
            cli, ["spaces", "members", "space-1", "-p", "2", "-l", "25"]
        )
        assert result.exit_code == 0


class TestSpacesMembersAddCommand:
    """Tests for spaces members-add command."""

    def test_add_members_to_space(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Add members to space."""
        httpx_mock.add_response(json={"success": True})

        result = runner.invoke(
            cli, ["spaces", "members-add", "space-1", "--user-ids", "user-1,user-2"]
        )
        assert result.exit_code == 0
        assert "Added 2 member(s)" in result.output

    def test_add_members_with_role(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Add members with specific role."""
        httpx_mock.add_response(json={"success": True})

        result = runner.invoke(
            cli,
            ["spaces", "members-add", "space-1", "-u", "user-1", "-r", "admin"],
        )
        assert result.exit_code == 0


class TestSpacesMembersRemoveCommand:
    """Tests for spaces members-remove command."""

    def test_remove_member_from_space(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Remove member from space."""
        httpx_mock.add_response(json={})

        result = runner.invoke(
            cli, ["spaces", "members-remove", "space-1", "--user-id", "user-1"]
        )
        assert result.exit_code == 0
        assert "Removed user 'user-1'" in result.output

    def test_remove_member_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Remove member handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "User not in space"})

        result = runner.invoke(
            cli, ["spaces", "members-remove", "space-1", "-u", "nonexistent"]
        )
        assert result.exit_code == 1
        assert "User not in space" in result.output


class TestSpacesMembersChangeRoleCommand:
    """Tests for spaces members-change-role command."""

    def test_change_role_for_user(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Change role for a user."""
        httpx_mock.add_response(json={"success": True})

        result = runner.invoke(
            cli,
            ["spaces", "members-change-role", "space-1", "--user-id", "user-1", "--role", "admin"],
        )
        assert result.exit_code == 0
        assert "Changed role for user 'user-1'" in result.output
        assert "to 'admin'" in result.output

    def test_change_role_for_group(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Change role for a group."""
        httpx_mock.add_response(json={"success": True})

        result = runner.invoke(
            cli,
            ["spaces", "members-change-role", "space-1", "-g", "group-1", "-r", "editor"],
        )
        assert result.exit_code == 0
        assert "Changed role for group 'group-1'" in result.output
        assert "to 'editor'" in result.output

    def test_change_role_requires_user_or_group(
        self, runner: CliRunner, mock_auth
    ) -> None:
        """Change role requires --user-id or --group-id."""
        result = runner.invoke(
            cli, ["spaces", "members-change-role", "space-1", "--role", "admin"]
        )
        assert result.exit_code == 1
        assert "Either --user-id or --group-id must be provided" in result.output

    def test_change_role_requires_role(self, runner: CliRunner, mock_auth) -> None:
        """Change role requires --role option."""
        result = runner.invoke(
            cli, ["spaces", "members-change-role", "space-1", "--user-id", "user-1"]
        )
        assert result.exit_code == 2
        assert "Missing option" in result.output or "--role" in result.output

    def test_change_role_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Change role handles API error."""
        httpx_mock.add_response(status_code=400, json={"message": "Invalid role"})

        result = runner.invoke(
            cli,
            ["spaces", "members-change-role", "space-1", "-u", "user-1", "-r", "invalid"],
        )
        assert result.exit_code == 1
        assert "Invalid role" in result.output
