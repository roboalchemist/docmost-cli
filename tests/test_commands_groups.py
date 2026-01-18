"""Tests for groups commands."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from docmost.cli import cli


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


class TestGroupsListCommand:
    """Tests for groups list command."""

    def test_list_groups(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """List all groups."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "g1", "name": "Engineering", "memberCount": 10},
                    {"id": "g2", "name": "Marketing", "memberCount": 5},
                ]
            }
        )

        result = runner.invoke(cli, ["groups", "list"])
        assert result.exit_code == 0
        assert "Engineering" in result.output

    def test_list_groups_with_query(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Search groups."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["groups", "list", "-q", "eng"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b"query=eng" in request.content

    def test_list_groups_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List groups with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["groups", "list", "-p", "2", "-l", "25"])
        assert result.exit_code == 0

    def test_list_groups_handles_groups_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List handles 'groups' key."""
        httpx_mock.add_response(
            json={"groups": [{"id": "g1", "name": "Group 1"}]}
        )

        result = runner.invoke(cli, ["groups", "list"])
        assert result.exit_code == 0


class TestGroupsInfoCommand:
    """Tests for groups info command."""

    def test_group_info(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get group info."""
        httpx_mock.add_response(
            json={"id": "g-123", "name": "Engineering", "description": "Dev team"}
        )

        result = runner.invoke(cli, ["groups", "info", "g-123"])
        assert result.exit_code == 0
        assert "Engineering" in result.output

    def test_group_info_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Group info handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "Group not found"})

        result = runner.invoke(cli, ["groups", "info", "nonexistent"])
        assert result.exit_code == 1
        assert "Group not found" in result.output


class TestGroupsCreateCommand:
    """Tests for groups create command."""

    def test_create_group(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Create a new group."""
        httpx_mock.add_response(json={"id": "new-group", "name": "New Group"})

        result = runner.invoke(cli, ["groups", "create", "--name", "New Group"])
        assert result.exit_code == 0
        assert "Group 'New Group' created" in result.output

    def test_create_group_with_description(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create group with description."""
        httpx_mock.add_response(json={"id": "g1", "name": "G1"})

        result = runner.invoke(
            cli, ["groups", "create", "-n", "G1", "-d", "Group description"]
        )
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b"description=Group+description" in request.content

    def test_create_group_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create group handles error."""
        httpx_mock.add_response(status_code=400, json={"message": "Name already exists"})

        result = runner.invoke(cli, ["groups", "create", "-n", "Existing"])
        assert result.exit_code == 1
        assert "Name already exists" in result.output


class TestGroupsUpdateCommand:
    """Tests for groups update command."""

    def test_update_group_name(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update group name."""
        httpx_mock.add_response(json={"id": "g-1", "name": "Updated Name"})

        result = runner.invoke(
            cli, ["groups", "update", "g-1", "--name", "Updated Name"]
        )
        assert result.exit_code == 0
        assert "Group 'g-1' updated" in result.output

    def test_update_group_description(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update group description."""
        httpx_mock.add_response(json={"id": "g-1"})

        result = runner.invoke(
            cli, ["groups", "update", "g-1", "-d", "New description"]
        )
        assert result.exit_code == 0


class TestGroupsDeleteCommand:
    """Tests for groups delete command."""

    def test_delete_group_with_force(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete group with --force flag."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["groups", "delete", "g-1", "--force"])
        assert result.exit_code == 0
        assert "Group 'g-1' deleted" in result.output

    def test_delete_group_with_confirmation(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Delete group with confirmation."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["groups", "delete", "g-1"], input="y\n")
        assert result.exit_code == 0

    def test_delete_group_cancelled(self, runner: CliRunner, mock_auth) -> None:
        """Delete group cancelled by user."""
        result = runner.invoke(cli, ["groups", "delete", "g-1"], input="n\n")
        assert result.exit_code == 0
        assert "Cancelled" in result.output


class TestGroupsMembersCommand:
    """Tests for groups members command."""

    def test_list_group_members(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List group members."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "u1", "name": "Alice", "email": "alice@example.com"},
                    {"id": "u2", "name": "Bob", "email": "bob@example.com"},
                ]
            }
        )

        result = runner.invoke(cli, ["groups", "members", "g-1"])
        assert result.exit_code == 0
        assert "Alice" in result.output

    def test_list_group_members_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List members with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["groups", "members", "g-1", "-p", "2", "-l", "25"])
        assert result.exit_code == 0

    def test_list_group_members_handles_members_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List members handles 'members' key."""
        httpx_mock.add_response(
            json={"members": [{"id": "u1", "name": "User 1"}]}
        )

        result = runner.invoke(cli, ["groups", "members", "g-1"])
        assert result.exit_code == 0


class TestGroupsMembersAddCommand:
    """Tests for groups members-add command."""

    def test_add_members_to_group(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Add members to group."""
        httpx_mock.add_response(json={"success": True})

        result = runner.invoke(
            cli, ["groups", "members-add", "g-1", "--user-ids", "u1,u2,u3"]
        )
        assert result.exit_code == 0
        assert "Added 3 member(s)" in result.output

    def test_add_single_member(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Add single member."""
        httpx_mock.add_response(json={"success": True})

        result = runner.invoke(cli, ["groups", "members-add", "g-1", "-u", "u1"])
        assert result.exit_code == 0
        assert "Added 1 member(s)" in result.output


class TestGroupsMembersRemoveCommand:
    """Tests for groups members-remove command."""

    def test_remove_member_from_group(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Remove member from group."""
        httpx_mock.add_response(json={})

        result = runner.invoke(
            cli, ["groups", "members-remove", "g-1", "--user-id", "u1"]
        )
        assert result.exit_code == 0
        assert "Removed user 'u1'" in result.output

    def test_remove_member_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Remove member handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "User not in group"})

        result = runner.invoke(
            cli, ["groups", "members-remove", "g-1", "-u", "nonexistent"]
        )
        assert result.exit_code == 1
        assert "User not in group" in result.output
