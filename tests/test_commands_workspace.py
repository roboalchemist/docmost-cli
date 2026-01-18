"""Tests for workspace commands."""

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


class TestWorkspaceInfoCommand:
    """Tests for workspace info command."""

    def test_workspace_info(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get workspace info."""
        httpx_mock.add_response(
            json={
                "id": "ws-123",
                "name": "My Workspace",
                "description": "Test workspace",
            }
        )

        result = runner.invoke(cli, ["workspace", "info"])
        assert result.exit_code == 0
        assert "My Workspace" in result.output

    def test_workspace_info_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Workspace info handles error."""
        httpx_mock.add_response(status_code=500, json={"message": "Server error"})

        result = runner.invoke(cli, ["workspace", "info"])
        assert result.exit_code == 1


class TestWorkspacePublicCommand:
    """Tests for workspace public command."""

    def test_workspace_public(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get public workspace info."""
        httpx_mock.add_response(
            json={
                "id": "ws-123",
                "name": "Public Workspace",
                "isPublic": True,
            }
        )

        result = runner.invoke(cli, ["workspace", "public"])
        assert result.exit_code == 0
        assert "Public Workspace" in result.output

    def test_workspace_public_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Workspace public handles error."""
        httpx_mock.add_response(status_code=500, json={"message": "Server error"})

        result = runner.invoke(cli, ["workspace", "public"])
        assert result.exit_code == 1


class TestWorkspaceUpdateCommand:
    """Tests for workspace update command."""

    def test_update_workspace_name(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update workspace name."""
        httpx_mock.add_response(json={"id": "ws-1", "name": "New Name"})

        result = runner.invoke(cli, ["workspace", "update", "--name", "New Name"])
        assert result.exit_code == 0
        assert "Workspace updated" in result.output

    def test_update_workspace_description(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update workspace description."""
        httpx_mock.add_response(json={"id": "ws-1"})

        result = runner.invoke(
            cli, ["workspace", "update", "-d", "New description"]
        )
        assert result.exit_code == 0

    def test_update_workspace_logo(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Update workspace logo."""
        httpx_mock.add_response(json={"id": "ws-1"})

        result = runner.invoke(
            cli, ["workspace", "update", "--logo", "https://example.com/logo.png"]
        )
        assert result.exit_code == 0


class TestWorkspaceMembersCommand:
    """Tests for workspace members command."""

    def test_list_workspace_members(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List workspace members."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "u1", "name": "Alice", "email": "alice@example.com", "role": "admin"},
                    {"id": "u2", "name": "Bob", "email": "bob@example.com", "role": "member"},
                ]
            }
        )

        result = runner.invoke(cli, ["workspace", "members"])
        assert result.exit_code == 0
        assert "Alice" in result.output

    def test_list_workspace_members_with_query(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Search workspace members."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["workspace", "members", "-q", "alice"])
        assert result.exit_code == 0

        request = httpx_mock.get_request()
        assert b"query=alice" in request.content

    def test_list_workspace_members_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List members with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(cli, ["workspace", "members", "-p", "2", "-l", "25"])
        assert result.exit_code == 0

    def test_list_workspace_members_handles_members_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List members handles 'members' key."""
        httpx_mock.add_response(
            json={"members": [{"id": "u1", "name": "User 1"}]}
        )

        result = runner.invoke(cli, ["workspace", "members"])
        assert result.exit_code == 0


class TestWorkspaceMembersChangeRoleCommand:
    """Tests for workspace members-change-role command."""

    def test_change_member_role(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Change member role."""
        httpx_mock.add_response(json={})

        result = runner.invoke(
            cli, ["workspace", "members-change-role", "user-123", "--role", "admin"]
        )
        assert result.exit_code == 0
        assert "Changed role for user 'user-123' to 'admin'" in result.output

    def test_change_member_role_short_option(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Change member role with short option."""
        httpx_mock.add_response(json={})

        result = runner.invoke(
            cli, ["workspace", "members-change-role", "user-456", "-r", "member"]
        )
        assert result.exit_code == 0
        assert "Changed role for user 'user-456' to 'member'" in result.output

    def test_change_member_role_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Change member role handles error."""
        httpx_mock.add_response(status_code=404, json={"message": "User not found"})

        result = runner.invoke(
            cli, ["workspace", "members-change-role", "invalid-user", "--role", "admin"]
        )
        assert result.exit_code == 1
        assert "User not found" in result.output

    def test_change_member_role_missing_role(
        self, runner: CliRunner, mock_auth
    ) -> None:
        """Change member role requires --role option."""
        result = runner.invoke(cli, ["workspace", "members-change-role", "user-123"])
        assert result.exit_code == 2
        assert "Missing option" in result.output or "--role" in result.output


class TestWorkspaceInvitesListCommand:
    """Tests for workspace invites list command."""

    def test_list_invites(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """List pending invitations."""
        httpx_mock.add_response(
            json={
                "items": [
                    {"id": "inv-1", "email": "new@example.com", "role": "member"},
                ]
            }
        )

        result = runner.invoke(cli, ["workspace", "invites", "list"])
        assert result.exit_code == 0
        assert "new@example.com" in result.output

    def test_list_invites_pagination(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List invites with pagination."""
        httpx_mock.add_response(json={"items": []})

        result = runner.invoke(
            cli, ["workspace", "invites", "list", "-p", "2", "-l", "10"]
        )
        assert result.exit_code == 0

    def test_list_invites_handles_invitations_key(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """List invites handles 'invitations' key."""
        httpx_mock.add_response(
            json={"invitations": [{"id": "inv-1", "email": "user@example.com"}]}
        )

        result = runner.invoke(cli, ["workspace", "invites", "list"])
        assert result.exit_code == 0


class TestWorkspaceInvitesCreateCommand:
    """Tests for workspace invites create command."""

    def test_create_invite(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Create workspace invitation."""
        httpx_mock.add_response(json={"success": True})

        result = runner.invoke(
            cli,
            [
                "workspace",
                "invites",
                "create",
                "--emails",
                "new1@example.com,new2@example.com",
                "--role",
                "member",
            ],
        )
        assert result.exit_code == 0
        assert "Invited 2 user(s)" in result.output

    def test_create_invite_single_email(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create invitation for single email."""
        httpx_mock.add_response(json={"success": True})

        result = runner.invoke(
            cli,
            ["workspace", "invites", "create", "-e", "user@example.com", "-r", "admin"],
        )
        assert result.exit_code == 0
        assert "Invited 1 user(s)" in result.output

    def test_create_invite_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Create invite handles error."""
        httpx_mock.add_response(status_code=400, json={"message": "Invalid email"})

        result = runner.invoke(
            cli, ["workspace", "invites", "create", "-e", "invalid", "-r", "member"]
        )
        assert result.exit_code == 1
        assert "Invalid email" in result.output


class TestWorkspaceInvitesRevokeCommand:
    """Tests for workspace invites revoke command."""

    def test_revoke_invite(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Revoke pending invitation."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["workspace", "invites", "revoke", "inv-123"])
        assert result.exit_code == 0
        assert "Invitation 'inv-123' revoked" in result.output

    def test_revoke_invite_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Revoke invite handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "Invitation not found"})

        result = runner.invoke(cli, ["workspace", "invites", "revoke", "nonexistent"])
        assert result.exit_code == 1
        assert "Invitation not found" in result.output


class TestWorkspaceInvitesResendCommand:
    """Tests for workspace invites resend command."""

    def test_resend_invite(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Resend pending invitation."""
        httpx_mock.add_response(json={})

        result = runner.invoke(cli, ["workspace", "invites", "resend", "inv-123"])
        assert result.exit_code == 0
        assert "Invitation 'inv-123' resent" in result.output

    def test_resend_invite_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Resend invite handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "Invitation not found"})

        result = runner.invoke(cli, ["workspace", "invites", "resend", "nonexistent"])
        assert result.exit_code == 1
        assert "Invitation not found" in result.output

    def test_resend_invite_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Resend invite handles server error."""
        httpx_mock.add_response(status_code=500, json={"message": "Server error"})

        result = runner.invoke(cli, ["workspace", "invites", "resend", "inv-123"])
        assert result.exit_code == 1


class TestWorkspaceInvitesInfoCommand:
    """Tests for workspace invites info command."""

    def test_invite_info(self, runner: CliRunner, httpx_mock, mock_auth) -> None:
        """Get invitation info."""
        httpx_mock.add_response(
            json={
                "id": "inv-123",
                "email": "user@example.com",
                "role": "member",
                "status": "pending",
                "createdAt": "2026-01-15T00:00:00Z",
            }
        )

        result = runner.invoke(cli, ["workspace", "invites", "info", "inv-123"])
        assert result.exit_code == 0
        assert "user@example.com" in result.output

    def test_invite_info_not_found(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Get invite info handles not found."""
        httpx_mock.add_response(status_code=404, json={"message": "Invitation not found"})

        result = runner.invoke(cli, ["workspace", "invites", "info", "nonexistent"])
        assert result.exit_code == 1
        assert "Invitation not found" in result.output

    def test_invite_info_error(
        self, runner: CliRunner, httpx_mock, mock_auth
    ) -> None:
        """Get invite info handles server error."""
        httpx_mock.add_response(status_code=500, json={"message": "Server error"})

        result = runner.invoke(cli, ["workspace", "invites", "info", "inv-123"])
        assert result.exit_code == 1
