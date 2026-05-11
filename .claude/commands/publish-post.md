Publish a blog post from The Gigi Zone to Medium as a draft.

## Steps

1. If the user didn't specify a post path, look at the most recently modified post under `content/posts/` and confirm with the user before publishing.

2. Verify the post exists at `content/posts/<post_path>/index.md`.

3. **Pre-flight: confirm the post is live on GitHub Pages first.** `gzctl` rewrites relative image paths to absolute `the-gigi.github.io/gigi-zone/...` URLs, so Medium's image importer needs those URLs reachable. Skip this step only with explicit user opt-out.
   - Confirm there are no unpushed commits that touch the post (`git status` clean and `git log origin/main..HEAD -- content/posts/<post_path>` empty).
   - Probe the hero image until it returns 200: `curl -sI https://the-gigi.github.io/gigi-zone/posts/<post_path>/images/hero.png | head -1`. Poll every ~15s for up to ~3 min; the typical Pages deploy is 60-90s. If it 404s past that, surface the GitHub Actions status to the user.

4. **Pre-flight: sweep `--` in H2/H3 headings.** Medium converts `--` to em-dash in headings (the `## kubectl get --raw` → `kubectl get—raw` bug). Grep for `^##.*--` in the post; if any hits, wrap the affected token in backticks before publishing. Spaced ` - ` is safe because `gzctl` already handles it.

5. Run the publish command:
   ```bash
   cd /Users/gigi/git/gigi-zone && uv run tools/gzctl/gzctl.py publish-py <post_path>
   ```
   If `gzctl`'s link checker fails on Amazon book links (Amazon returns 405 to HEAD), re-run with `--skip-links`.

6. Report the resulting Medium draft URL to the user.

7. If this is a **re-publish** after edits, remind the user that Medium creates a new draft each time — they should delete the stale draft from Medium manually.

## Prerequisites

- `MEDIUM_TOKEN` must be set in `tools/gzctl/.env`
- The `uv` package manager must be available

## Notes

- This publishes as a **draft** on Medium, not a public post. The user still needs to review and publish manually on Medium.
- There is also a `publish` command (uses Claude Agent SDK for conversion) but `publish-py` is faster and doesn't spawn a subprocess.
- See the "Medium Publishing Gotchas" section in the project `CLAUDE.md` for the full background on the image-deploy race and the `--`/em-dash issue.
