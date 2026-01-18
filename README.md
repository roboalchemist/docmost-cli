# docmost-cli

A CLI tool for interacting with the [Docmost](https://docmost.com) API.

## Installation

```bash
pip install docmost-cli
```

Or install from source:

```bash
git clone https://gitea.roboalch.com/gateway/docmost-cli
cd docmost-cli
pip install -e .
```

## Configuration

Create a configuration file at `~/.config/docmost/config.yaml`:

```yaml
url: https://docs.example.com/api
default_format: table
```

Or set environment variables:

```bash
export DOCMOST_URL=https://docs.example.com/api
export DOCMOST_TOKEN=your-access-token
```

## Authentication

Login to store your access token:

```bash
docmost login
```

This will prompt for your email and password, then store the token securely.

## Usage

### Spaces

```bash
# List all spaces
docmost spaces list

# Get space info
docmost spaces info SPACE_ID

# Create a space
docmost spaces create --name "My Space" --slug my-space

# Update a space
docmost spaces update SPACE_ID --name "New Name"

# Delete a space
docmost spaces delete SPACE_ID
```

### Pages

```bash
# Create a page
docmost pages create --space-id SPACE_ID --title "My Page"

# Get page info
docmost pages info PAGE_ID

# Update a page
docmost pages update PAGE_ID --title "New Title"

# Delete a page
docmost pages delete PAGE_ID

# Get page tree for a space
docmost pages tree SPACE_ID

# Export a page
docmost pages export PAGE_ID --format markdown
```

### Search

```bash
# Search content
docmost search "query"

# Search with suggestions
docmost search suggest "query" --include-users
```

### Users

```bash
# Get current user info
docmost users me

# Update user
docmost users update USER_ID --name "New Name"
```

### Workspace

```bash
# Get workspace info
docmost workspace info

# List workspace members
docmost workspace members
```

### Groups

```bash
# List groups
docmost groups list

# Create a group
docmost groups create --name "My Group"
```

### Comments

```bash
# List comments on a page
docmost comments list PAGE_ID

# Create a comment
docmost comments create PAGE_ID --content "My comment"
```

## Output Formats

Use `--format` to change output format:

```bash
docmost spaces list --format json
docmost spaces list --format table
docmost spaces list --format plain
```

## License

MIT
