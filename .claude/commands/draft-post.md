Draft a new blog post for The Gigi Zone.

## Steps

1. Figure out what the user wants to write about from the conversation context. If the title, topic, or series installment number isn't clear, ask.

2. Determine the correct slug for the post directory. Look at existing posts under `content/posts/` to detect naming patterns (e.g. series with numbered slugs like `cc-deep-dive-NN-slug`). Derive the slug from the title and any series conventions found.

3. Use today's date to determine year/month: `content/posts/<YEAR>/<MONTH>/<slug>/`

4. Create the post directory with an `images/` subdirectory.

5. Write the full post content in `index.md` with proper TOML front matter.

6. Follow the writing style guide and content structure from the project's CLAUDE.md. Pay special attention to:
   - TOML front matter format
   - `<!--more-->` excerpt cutoff placement
   - Series-specific structure (e.g. CCDD series has emoji-bookend H2 headers, series index, What's Next, Take Home Points, closing greeting)

7. Look at the most recent posts in the same series (if applicable) for structural reference: series index links, closing greeting language rotation, "What's Next" topics.

8. If the topic references diagrams or images, add placeholder image references (`![](images/placeholder-name.png)`) so the user knows what visuals to create.

## Spec File Convention

Specs can be stored in `tools/gzctl/blog_specs/` for reference. If the user provides a spec file path, read it. Example spec format:

```
CCDD #11. Slug: cc-deep-dive-11-loop-the-loop.

The article covers recurring tasks with /loop.

Key content points:
1. What /loop does and why it exists
2. Syntax and parameters
...

Keep under 2500 words. Swahili closing greeting.
```
