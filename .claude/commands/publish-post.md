Publish a blog post from The Gigi Zone to Medium as a draft.

## Steps

1. If the user didn't specify a post path, look at the most recently modified post under `content/posts/` and confirm with the user before publishing.

2. Verify the post exists at `content/posts/<post_path>/index.md`.

3. Run the publish command:
   ```bash
   cd /Users/gigi/git/gigi-zone && uv run tools/gzctl/gzctl.py publish-py <post_path>
   ```

4. Report the resulting Medium draft URL to the user.

## Prerequisites

- `MEDIUM_TOKEN` must be set in `tools/gzctl/.env`
- The `uv` package manager must be available

## Notes

- This publishes as a **draft** on Medium, not a public post. The user still needs to review and publish manually on Medium.
- There is also a `publish` command (uses Claude Agent SDK for conversion) but `publish-py` is faster and doesn't spawn a subprocess.
