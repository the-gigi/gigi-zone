# gzctl

CLI tool for managing the Gigi Zone blog, powered by the Claude Agent SDK.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (runs the script with inline dependencies)
- A `MEDIUM_TOKEN` in `tools/gzctl/.env` (required for the `publish` commands)

## Commands

### draft

Generate a new blog post draft using Claude.

```bash
# Provide the spec inline
uv run tools/gzctl/gzctl.py draft "My Post Title" "Write about topic X, covering Y and Z"

# Or read the spec from a file
uv run tools/gzctl/gzctl.py draft "My Post Title" -f tools/gzctl/blog_specs/my-spec.txt
```

### publish

Publish a Hugo blog post to Medium as a draft. Uses Claude (via the Agent SDK) to convert the post to Medium format, then publishes through an in-process MCP server wrapping the Medium API. The agent handles conversion edge cases better than regex.

```bash
uv run tools/gzctl/gzctl.py publish 2026/03/cc-deep-dive-10-sdk-strikes-back
```

### publish-py

Pure Python alternative that skips the Agent SDK entirely. Same conversion, direct Medium API call. Faster but doesn't use MCP.

```bash
uv run tools/gzctl/gzctl.py publish-py 2026/03/cc-deep-dive-10-sdk-strikes-back
```

The argument is the post path relative to `content/posts/`.
