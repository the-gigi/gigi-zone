# /// script
# requires-python = ">=3.12"
# dependencies = ["claude-agent-sdk", "click", "python-dotenv", "medium"]
# ///

"""gzctl - CLI tool for managing the Gigi Zone blog."""

import asyncio
import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path

import click
from dotenv import load_dotenv
from medium import Client as MediumClient

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

GIGI_ZONE_DIR = Path(__file__).resolve().parent.parent.parent
GZCTL_DIR = Path(__file__).resolve().parent
GIGI_ZONE_BASE_URL = "https://the-gigi.github.io/gigi-zone/posts"

load_dotenv(GZCTL_DIR / ".env")


def _convert_post(post_path: str) -> dict:
    """Convert a Hugo blog post to Medium format. Pure Python, no agent needed."""
    post_dir = GIGI_ZONE_DIR / "content" / "posts" / post_path
    index_file = post_dir / "index.md"

    if not index_file.exists():
        raise click.ClickException(f"Post not found: {index_file}")

    content = index_file.read_text()
    free_link_url = f"{GIGI_ZONE_BASE_URL}/{post_path}/"

    # Extract front matter
    match = re.match(r"\+\+\+\n(.*?)\n\+\+\+\n", content, re.DOTALL)
    if not match:
        raise click.ClickException("Could not parse TOML front matter")

    front_matter = match.group(1)
    body = content[match.end():]

    # Extract title
    title_match = re.search(r"title\s*=\s*'([^']*)'", front_matter)
    if not title_match:
        title_match = re.search(r'title\s*=\s*"([^"]*)"', front_matter)
    if not title_match:
        raise click.ClickException("Could not extract title from front matter")
    title = title_match.group(1)

    # Extract categories as tags (max 5)
    cats_match = re.search(r"categories\s*=\s*\[([^\]]*)\]", front_matter)
    tags = []
    if cats_match:
        tags = [c.strip().strip("'\"") for c in cats_match.group(1).split(",")][:5]

    # Add free link as first line
    free_link = f'🔓 **Not a Medium member? [Read this article for free on The Gigi Zone]({free_link_url})** 🔓'
    body = free_link + "\n" + body

    # Remove <!--more-->
    body = body.replace("<!--more-->\n", "")
    body = body.replace("<!--more-->", "")

    # Convert relative image links to absolute URLs
    body = re.sub(
        r"!\[([^\]]*)\]\(images/",
        rf"![\1]({free_link_url}images/",
        body,
    )

    # Remove HTML tags (like <img> lines)
    body = re.sub(r"<img[^>]*>", "", body)

    # Collapse more than 2 consecutive blank lines into 2 (outside code blocks)
    parts = re.split(r"(```.*?```)", body, flags=re.DOTALL)
    for i in range(0, len(parts), 2):  # only non-code parts
        parts[i] = re.sub(r"\n{3,}", "\n\n", parts[i])
    body = "".join(parts)

    return {"title": title, "content": body.strip(), "tags": tags}


def _publish_to_medium(title: str, content: str, tags: list[str]) -> dict:
    """Publish content to Medium as a draft. Direct API call, no agent."""
    token = os.environ.get("MEDIUM_TOKEN")
    if not token:
        raise click.ClickException("Set MEDIUM_TOKEN in tools/gzctl/.env")

    client = MediumClient(access_token=token)
    user = client.get_current_user()

    # Medium converts " - " to em-dash. Insert a zero-width space
    # after the hyphen to prevent this. Renders identically.
    title = title.replace(" - ", " -\u200b ")
    content = content.replace(" - ", " -\u200b ")

    post = client.create_post(
        user_id=user["id"],
        title=title,
        content=content,
        content_format="markdown",
        tags=tags,
        publish_status="draft",
    )
    return post


@click.group()
def cli():
    """gzctl - CLI tool for managing the Gigi Zone blog."""
    pass


@cli.command()
@click.argument("title")
@click.argument("spec", required=False)
@click.option("--spec-file", "-f", type=click.Path(exists=True), help="Read spec from a file")
def draft(title: str, spec: str | None, spec_file: str | None):
    """Generate a blog post draft.

    TITLE is the post title.
    SPEC describes what the post should cover.
    Provide SPEC as an argument or use --spec-file/-f to read from a file.
    """
    if spec_file:
        spec = Path(spec_file).read_text().strip()
    if not spec:
        raise click.ClickException("Provide SPEC as an argument or use --spec-file/-f")
    asyncio.run(_draft(title, spec))


async def _draft(title: str, spec: str):
    today = date.today()
    year = today.strftime("%Y")
    month = today.strftime("%m")

    prompt = f"""Create a new blog post with:
- Title: {title}
- Spec: {spec}
- Year/month for the post directory: {year}/{month}

Determine the correct slug for the post directory. Look at existing posts under
content/posts/ to detect naming patterns (e.g. series with numbered slugs).
If the spec mentions a slug, use that. Otherwise derive one from the title and
any series conventions you find.

Create the post directory at content/posts/{year}/{month}/<slug>/ with an
images/ subdirectory, and write the full post content in index.md with proper
TOML front matter.

Follow the writing style guide and content structure from the project's CLAUDE.md.
"""

    click.echo(f"Generating draft: {title}")
    click.echo()

    options = ClaudeAgentOptions(
        cwd=str(GIGI_ZONE_DIR),
        allowed_tools=["Read", "Write", "Bash", "Glob"],
        permission_mode="acceptEdits",
        max_turns=10,
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    click.echo(block.text)
                elif isinstance(block, ToolUseBlock):
                    click.echo(f"[tool] {block.name}", err=True)
                elif isinstance(block, ToolResultBlock):
                    if block.is_error:
                        click.echo(f"[tool error] {block.content}", err=True)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                click.echo(f"\nError: {message.result}", err=True)
            else:
                click.echo("\nDraft created successfully!")


@cli.command()
@click.argument("post_path")
def publish(post_path: str):
    """Publish a Hugo blog post to Medium using the Agent SDK.

    Uses Claude to convert the post, then publishes through an in-process
    MCP server wrapping the Medium API.

    POST_PATH is the path to the post's index.md file,
    relative to the gigi-zone content directory.
    For example: 2026/03/cc-deep-dive-10-sdk-strikes-back
    """
    post_dir = GIGI_ZONE_DIR / "content" / "posts" / post_path
    index_file = post_dir / "index.md"
    if not index_file.exists():
        raise click.ClickException(f"Post not found: {index_file}")

    click.echo(f"Publishing to Medium: {post_path}")
    click.echo()

    # Step 1: Convert via Agent SDK
    click.echo("Converting via Agent SDK...", err=True)
    converted = asyncio.run(_agent_convert(post_path, index_file))

    if not converted.get("title"):
        click.echo("Agent failed to produce converted content.", err=True)
        raise SystemExit(1)

    title = converted["title"]
    content = converted["content"]
    tags = converted["tags"]

    click.echo(f"  Title: {title}", err=True)
    click.echo(f"  Tags: {tags}", err=True)
    click.echo(f"  Content length: {len(content)} chars", err=True)

    # Step 2: Publish via MCP
    click.echo("Publishing via MCP...", err=True)
    result = asyncio.run(_publish_mcp(title, content, tags))

    if result.get("success"):
        click.echo(f"\nPublished to Medium as draft: {result['url']}")
    else:
        click.echo(f"\nFailed to publish: {result.get('error', 'unknown')}", err=True)
        raise SystemExit(1)


@cli.command("publish-py")
@click.argument("post_path")
def publish_py(post_path: str):
    """Publish a Hugo blog post to Medium using pure Python (no agent).

    Faster alternative that skips the Agent SDK entirely.

    POST_PATH is the path to the post's index.md file,
    relative to the gigi-zone content directory.
    For example: 2026/03/cc-deep-dive-10-sdk-strikes-back
    """
    click.echo(f"Publishing to Medium: {post_path}")
    click.echo()

    click.echo("Converting...", err=True)
    try:
        converted = _convert_post(post_path)
    except Exception as e:
        click.echo(f"Conversion failed: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"  Title: {converted['title']}", err=True)
    click.echo(f"  Tags: {converted['tags']}", err=True)
    click.echo(f"  Content length: {len(converted['content'])} chars", err=True)

    click.echo("Publishing...", err=True)
    try:
        post = _publish_to_medium(
            converted["title"], converted["content"], converted["tags"]
        )
    except Exception as e:
        click.echo(f"Publish failed: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"\nPublished to Medium as draft: {post['url']}")


async def _agent_convert(post_path: str, index_file: Path) -> dict:
    """Use the Agent SDK to convert a Hugo post to Medium-ready markdown."""
    free_link_url = f"{GIGI_ZONE_BASE_URL}/{post_path}/"
    tmp_dir = GZCTL_DIR / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    output_file = tmp_dir / "converted.md"
    output_file.unlink(missing_ok=True)

    # Extract title and tags in Python (reliable, no agent needed)
    raw = index_file.read_text()
    fm_match = re.match(r"\+\+\+\n(.*?)\n\+\+\+\n", raw, re.DOTALL)
    if not fm_match:
        raise click.ClickException("Could not parse TOML front matter")
    front_matter = fm_match.group(1)

    title_match = re.search(r"title\s*=\s*'([^']*)'", front_matter)
    if not title_match:
        title_match = re.search(r'title\s*=\s*"([^"]*)"', front_matter)
    if not title_match:
        raise click.ClickException("Could not extract title")
    title = title_match.group(1)

    cats_match = re.search(r"categories\s*=\s*\[([^\]]*)\]", front_matter)
    tags = []
    if cats_match:
        tags = [c.strip().strip("'\"") for c in cats_match.group(1).split(",")][:5]

    # Agent converts content and writes to file
    prompt = f"""Convert a Hugo blog post to Medium-ready markdown.

Read the post at: {index_file}

Conversion rules:
1. Strip the TOML front matter (+++ blocks) entirely
2. Add this free link as the VERY FIRST LINE, before anything else:
   🔓 **Not a Medium member? [Read this article for free on The Gigi Zone]({free_link_url})** 🔓
3. Remove the <!--more--> line
4. Convert relative image links like ![](images/foo.png) to absolute URLs:
   ![]({free_link_url}images/foo.png)
5. Remove any HTML tags like <img> lines
6. Collapse more than 2 consecutive blank lines into 2 (except inside code blocks)

Write the converted markdown to: {output_file}
"""

    options = ClaudeAgentOptions(
        cwd=str(GIGI_ZONE_DIR),
        allowed_tools=["Read", "Write"],
        permission_mode="acceptEdits",
        max_turns=5,
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    click.echo(block.text)
                elif isinstance(block, ToolUseBlock):
                    click.echo(f"[tool] {block.name}", err=True)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                click.echo(f"[agent error] {message.result}", err=True)

    if not output_file.exists():
        return {"title": None, "content": None, "tags": []}

    content = output_file.read_text().strip()
    output_file.unlink()
    return {"title": title, "content": content, "tags": tags}


async def _publish_mcp(title: str, content: str, tags: list[str]) -> dict:
    token = os.environ.get("MEDIUM_TOKEN")
    if not token:
        raise click.ClickException("Set MEDIUM_TOKEN in tools/gzctl/.env")

    client = MediumClient(access_token=token)
    user = client.get_current_user()

    # Write content to a temp file so the MCP tool can read it directly
    # (avoids the ~10KB MCP transport size limit on tool arguments)
    tmp_dir = GZCTL_DIR / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    content_file = tmp_dir / "to_publish.md"
    content_file.write_text(content)

    result = {"success": False, "url": None, "error": None}

    @tool(
        name="publish_draft",
        description="Publish a pre-prepared markdown article as a draft on Medium. "
        "The content is read from a temp file automatically. "
        "You only need to provide the title and tags.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Article title"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags (max 5)",
                },
            },
            "required": ["title"],
        },
    )
    async def publish_draft(args):
        pub_title = args["title"]
        pub_tags = args.get("tags", [])[:5]

        # Read content from the pre-written file
        pub_content = content_file.read_text()

        # Medium converts " - " to em-dash
        pub_title = pub_title.replace(" - ", " -\u200b ")
        pub_content = pub_content.replace(" - ", " -\u200b ")

        try:
            loop = asyncio.get_event_loop()
            post = await loop.run_in_executor(
                None,
                lambda: client.create_post(
                    user_id=user["id"],
                    title=pub_title,
                    content=pub_content,
                    content_format="markdown",
                    tags=pub_tags,
                    publish_status="draft",
                ),
            )
            result["success"] = True
            result["url"] = post["url"]
            return {
                "content": [
                    {"type": "text", "text": json.dumps({"id": post["id"], "url": post["url"]})}
                ]
            }
        except Exception as e:
            result["error"] = str(e)
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}

    server = create_sdk_mcp_server(name="medium", tools=[publish_draft])

    prompt = f"""Publish an article to Medium as a draft.

Call the publish_draft tool with:
- title: {json.dumps(title)}
- tags: {json.dumps(tags)}

The content is loaded automatically by the tool from a temp file. Do NOT pass content.
"""

    options = ClaudeAgentOptions(
        cwd=str(GIGI_ZONE_DIR),
        allowed_tools=["mcp__medium__publish_draft"],
        permission_mode="acceptEdits",
        max_turns=5,
        mcp_servers={"medium": server},
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    click.echo(block.text)
                elif isinstance(block, ToolUseBlock):
                    click.echo(f"[tool] {block.name}", err=True)
                elif isinstance(block, ToolResultBlock):
                    if block.is_error:
                        click.echo(f"[tool error] {str(block.content)[:300]}", err=True)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                click.echo(f"[agent error] {message.result}", err=True)

    content_file.unlink(missing_ok=True)
    return result


def _fetch_medium_stats() -> str:
    """Fetch Medium stats page content via Safari (requires logged-in session)."""
    script = '''
    tell application "Safari"
        if (count of windows) = 0 then
            make new document
        end if
        set newTab to make new tab at end of tabs of front window with properties {URL:"https://medium.com/me/stats"}
        set current tab of front window to newTab
        delay 8
        set pageText to do JavaScript "document.body.innerText" in newTab
        close newTab
        return pageText
    end tell
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise click.ClickException(
            f"Failed to fetch Medium stats: {result.stderr.strip()}"
        )
    return result.stdout


def _parse_medium_stats(raw: str) -> list[dict]:
    """Parse the raw text from Medium stats page into structured data."""
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]

    # Find the story stats section (after "Story\tPresentations" header area)
    stories = []
    i = 0
    while i < len(lines):
        # Look for lines that match a story title pattern followed by stats
        # Stories have: title, "·", "N min read", "·", date, "·", "View story",
        # then numbers (presentations, views, reads)
        if "min read" in lines[i] if i < len(lines) else False:
            # Back up to find the title (first non-metadata line before this)
            title_idx = i - 1
            while title_idx >= 0 and lines[title_idx] == "·":
                title_idx -= 1
            if title_idx < 0:
                i += 1
                continue

            title = lines[title_idx]

            # Scan forward past metadata to find the numbers
            j = i + 1
            while j < len(lines) and (lines[j] == "·" or "View story" in lines[j]
                                       or "2026" in lines[j] or "2025" in lines[j]
                                       or "2024" in lines[j]):
                j += 1

            # Collect numeric values
            nums = []
            while j < len(lines) and len(nums) < 3:
                val = lines[j].replace(",", "").replace("$", "")
                # Handle K notation (e.g., "5.1K")
                if val.upper().endswith("K"):
                    try:
                        nums.append(int(float(val[:-1]) * 1000))
                        j += 1
                        continue
                    except ValueError:
                        break
                try:
                    nums.append(int(float(val)))
                    j += 1
                except ValueError:
                    break

            if len(nums) >= 3:
                story = {
                    "title": title,
                    "presentations": nums[0],
                    "views": nums[1],
                    "reads": nums[2],
                }
                stories.append(story)

            i = j
        else:
            i += 1

    return stories


@cli.command()
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
@click.argument("title_filter", required=False)
def stats(json_output: bool, title_filter: str | None):
    """Fetch Medium story stats via Safari.

    Requires: Safari with 'Allow JavaScript from Apple Events' enabled
    and an active Medium login session.

    Optionally filter by TITLE_FILTER (case-insensitive substring match).
    """
    click.echo("Fetching Medium stats...", err=True)
    raw = _fetch_medium_stats()
    stories = _parse_medium_stats(raw)

    if not stories:
        raise click.ClickException("No story stats found. Are you logged in to Medium in Safari?")

    if title_filter:
        stories = [s for s in stories if title_filter.lower() in s["title"].lower()]

    # Clean up zero-width spaces and collapse multiple spaces in titles
    for s in stories:
        s["title"] = re.sub(r"\s+", " ", s["title"].replace("\u200b", " ")).strip()

    if json_output:
        click.echo(json.dumps(stories, indent=2))
    else:
        for s in stories:
            click.echo(f"{s['presentations']:>6} pres  {s['views']:>6} views  "
                       f"{s['reads']:>5} reads  {s['title']}")


if __name__ == "__main__":
    cli()
