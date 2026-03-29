Draft a new blog post for The Gigi Zone.

Arguments: `<title>` and either inline spec text or a path to a spec file.

## Steps

1. Parse the title and spec from the arguments. If a file path is provided, read the spec from that file.

2. Determine the correct slug for the post directory. Look at existing posts under `content/posts/` to detect naming patterns (e.g. series with numbered slugs like `cc-deep-dive-NN-slug`). Derive the slug from the title and any series conventions found.

3. Use today's date to determine year/month: `content/posts/<YEAR>/<MONTH>/<slug>/`

4. Create the post directory with an `images/` subdirectory.

5. Write the full post content in `index.md` with proper TOML front matter.

6. Follow the writing style guide and content structure from the project's CLAUDE.md. Pay special attention to:
   - TOML front matter format
   - `<!--more-->` excerpt cutoff placement
   - Series-specific structure (e.g. CCDD series has emoji-bookend H2 headers, series index, What's Next, Take Home Points, closing greeting)

7. Look at the most recent posts in the same series (if applicable) for structural reference: series index links, closing greeting language rotation, "What's Next" topics.

8. Generate all images referenced in the post (hero image, diagrams, etc.) using the `generate-image` skill. For each image:
   - Use the spec's description for the image prompt (style, colors, content)
   - Save directly to the post's `images/` directory with the correct filename
   - If no style guidance is given, default to clean diagrams with light backgrounds
   - Generate images in parallel when possible

## Spec File Convention

Specs can be stored in `tools/gzctl/blog_specs/` for reference. If the user provides a spec file path, read it. Example spec format:

```
CCDD #11. Slug: cc-deep-dive-11-on-the-clock.

The article covers recurring tasks in Claude Code.

Key content points:
1. What /loop does and why it exists
2. Syntax and parameters
...

Keep under 2500 words. Swahili closing greeting.
```
