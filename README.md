# docmost-cli

A CLI tool for interacting with the [Docmost](https://docmost.com) API.

## Installation

### Using pip

```bash
pip install docmost-cli
```

### From source

```bash
git clone https://gitea.roboalch.com/gateway/docmost-cli
cd docmost-cli
pip install -e .
```

### Development install

```bash
git clone https://gitea.roboalch.com/gateway/docmost-cli
cd docmost-cli
pip install -e ".[dev]"
```

## Configuration

### Config file

Create a configuration file at `~/.config/docmost/config.yaml`:

```yaml
url: https://docs.example.com/api
default_format: table
default_space: your-default-space-id
```

### Environment variables

Environment variables take precedence over config file settings:

| Variable | Description |
|----------|-------------|
| `DOCMOST_URL` | Docmost API URL (e.g., `https://docs.example.com/api`) |
| `DOCMOST_TOKEN` | Access token (overrides stored token) |
| `DOCMOST_FORMAT` | Default output format (`json`, `table`, or `plain`) |
| `DOCMOST_SPACE` | Default space ID for commands that require a space |

Example:

```bash
export DOCMOST_URL=https://docs.example.com/api
export DOCMOST_TOKEN=your-access-token
```

### Token storage

The access token is stored at `~/.config/docmost/token` with secure permissions (600). Use `docmost login` to store a token or set `DOCMOST_TOKEN` environment variable.

## Authentication

### Login

Authenticate and store your access token:

```bash
# Interactive login (prompts for credentials)
docmost login

# Non-interactive login
docmost login --url https://docs.example.com --email user@example.com --password yourpassword
```

### Logout

Remove the stored access token:

```bash
docmost logout
```

## Commands Reference

### Global Options

All commands support these global options:

```bash
docmost [OPTIONS] COMMAND
  -u, --url TEXT                  Docmost API URL
  -f, --format [json|table|plain] Output format
  -c, --config PATH               Config file path
  --version                       Show version
  --help                          Show help
```

### Spaces

Manage workspace spaces.

```bash
# List all spaces
docmost spaces list

# Get space information
docmost spaces info SPACE_ID

# Create a new space
docmost spaces create --name "My Space" --slug my-space
docmost spaces create --name "My Space" --slug my-space --description "Space description"

# Update a space
docmost spaces update SPACE_ID --name "New Name"
docmost spaces update SPACE_ID --description "New description" --icon "icon-name"

# Delete a space
docmost spaces delete SPACE_ID

# List space members
docmost spaces members SPACE_ID
docmost spaces members SPACE_ID --page 1 --limit 20

# Add members to a space
docmost spaces members-add SPACE_ID --user-ids "user1-id,user2-id"
docmost spaces members-add SPACE_ID --user-ids "user-id" --role admin

# Remove a member from a space
docmost spaces members-remove SPACE_ID --user-id user-id

# Change a member's role in a space
docmost spaces members-change-role SPACE_ID --user-id user-id --role writer
docmost spaces members-change-role SPACE_ID --group-id group-id --role admin
```

### Pages

Manage documentation pages.

```bash
# Create a new page
docmost pages create --space-id SPACE_ID --title "My Page"
docmost pages create --space-id SPACE_ID --title "My Page" --content "Page content"
docmost pages create --space-id SPACE_ID --title "Child Page" --parent-id PARENT_PAGE_ID

# Get page information
docmost pages info PAGE_ID

# Update a page
docmost pages update PAGE_ID --title "New Title"
docmost pages update PAGE_ID --content "Updated content"
docmost pages update PAGE_ID --icon "icon-name" --cover-photo "https://example.com/image.jpg"

# Delete a page
docmost pages delete PAGE_ID

# Move a page
docmost pages move PAGE_ID --parent-id NEW_PARENT_ID
docmost pages move PAGE_ID --after OTHER_PAGE_ID
docmost pages move PAGE_ID --before OTHER_PAGE_ID

# Get page tree (sidebar structure) for a space
docmost pages tree SPACE_ID

# Get recently updated pages
docmost pages recent
docmost pages recent --space-id SPACE_ID
docmost pages recent --page 1 --limit 10

# Export a page
docmost pages export PAGE_ID --format markdown
docmost pages export PAGE_ID --format html --output /path/to/file.html

# Get page revision history
docmost pages history PAGE_ID
docmost pages history PAGE_ID --page 1 --limit 20

# Get breadcrumb path for a page
docmost pages breadcrumbs PAGE_ID

# Get details of a specific history entry
docmost pages history-info HISTORY_ID
```

### Search

Search pages and content.

```bash
# Search across all spaces
docmost search "query"

# Search within a specific space
docmost search "query" --space-id SPACE_ID

# Paginated search
docmost search "query" --page 1 --limit 10
```

### Suggest

Get search suggestions (autocomplete).

```bash
# Basic suggestions
docmost suggest "query"

# Include users in suggestions
docmost suggest "query" --include-users

# Include groups in suggestions
docmost suggest "query" --include-groups
```

### Users

Manage users.

```bash
# Get current user information
docmost users me

# Update a user
docmost users update USER_ID --name "New Name"
docmost users update USER_ID --email "newemail@example.com"
docmost users update USER_ID --role admin
```

### Workspace

Manage workspace settings.

```bash
# Get workspace information
docmost workspace info

# Get public workspace information
docmost workspace public

# Update workspace settings
docmost workspace update --name "New Workspace Name"
docmost workspace update --description "Workspace description"
docmost workspace update --logo "https://example.com/logo.png"

# List workspace members
docmost workspace members

# Change a workspace member's role
docmost workspace members-change-role USER_ID --role admin

# Manage invitations
docmost workspace invites list
docmost workspace invites list --page 1 --limit 20
docmost workspace invites create --emails "user1@example.com,user2@example.com" --role member
docmost workspace invites revoke INVITATION_ID
docmost workspace invites info INVITATION_ID
docmost workspace invites resend INVITATION_ID
```

### Groups

Manage user groups.

```bash
# List all groups
docmost groups list

# Get group information
docmost groups info GROUP_ID

# Create a new group
docmost groups create --name "My Group"
docmost groups create --name "My Group" --description "Group description"

# Update a group
docmost groups update GROUP_ID --name "New Name"
docmost groups update GROUP_ID --description "New description"

# Delete a group
docmost groups delete GROUP_ID

# List group members
docmost groups members GROUP_ID
docmost groups members GROUP_ID --page 1 --limit 20

# Add members to a group
docmost groups members-add GROUP_ID --user-ids "user1-id,user2-id"

# Remove a member from a group
docmost groups members-remove GROUP_ID --user-id user-id
```

### Comments

Manage page comments.

```bash
# List comments on a page
docmost comments list PAGE_ID

# Get comment information
docmost comments info COMMENT_ID

# Create a comment
docmost comments create PAGE_ID --content "My comment"

# Create a reply to a comment
docmost comments create PAGE_ID --content "Reply text" --parent-id PARENT_COMMENT_ID

# Create a comment with text selection
docmost comments create PAGE_ID --content "Comment on selection" --selection '{"start": 0, "end": 10}'

# Update a comment
docmost comments update COMMENT_ID --content "Updated content"

# Resolve a comment
docmost comments resolve COMMENT_ID
docmost comments resolve COMMENT_ID --resolved

# Unresolve a comment
docmost comments resolve COMMENT_ID --unresolved

# Delete a comment
docmost comments delete COMMENT_ID
```

## Output Formats

Use `--format` (or `-f`) to change output format:

```bash
# JSON format (useful for scripting)
docmost spaces list --format json

# Table format (default, human-readable)
docmost spaces list --format table

# Plain format (minimal output)
docmost spaces list --format plain
```

You can set a default format in your config file or via `DOCMOST_FORMAT` environment variable.

## Troubleshooting

### Authentication errors

**"No token found"** - You need to authenticate first:
```bash
docmost login
```

**"Invalid token"** - Your token may have expired. Re-authenticate:
```bash
docmost logout
docmost login
```

### Connection errors

**"Connection refused"** - Check that your Docmost URL is correct:
```bash
# Verify URL (should point to API endpoint)
echo $DOCMOST_URL
# Should be like: https://docs.example.com/api
```

**"SSL certificate error"** - If using self-signed certificates, you may need to configure SSL verification in your environment.

### Permission errors

**"403 Forbidden"** - You don't have permission for this operation. Check:
- Your role in the workspace
- Your role in the specific space
- Whether the resource exists

### Common issues

**"Space not found"** - Verify the space ID:
```bash
docmost spaces list --format json
```

**"Page not found"** - Verify the page ID:
```bash
docmost pages tree SPACE_ID --format json
```

**Config file not loading** - Check file permissions and YAML syntax:
```bash
cat ~/.config/docmost/config.yaml
```

## License

MIT
