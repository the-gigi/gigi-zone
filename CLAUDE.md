## Project Overview

This is a Hugo static site blog (The Gigi Zone) using the Ananke theme, deployed to GitHub Pages via GitHub Actions.

## Common Commands

```bash
# Local development server
hugo serve

# Create a new post (adjust year/month/slug)
hugo new content content/posts/2026/01/new-post/index.md

# Create the images dir (adjust year/month/slug)
mkdir content/posts/2026/01/new-post/images
```

## Content Structure

Posts live in `content/posts/<YEAR>/<MONTH>/<SLUG>/index.md`. Each post directory can contain an `images/` subdirectory for post-specific assets.

### Front Matter Format (TOML)

```toml
+++
title = 'Post Title'
date = 2026-01-18T10:00:00-08:00
categories = ["Category1", "Category2"]
+++
```

- No need for `draft = true`. When ready to publish just push
- Use `<!--more-->` to mark the excerpt cutoff point
- Categories should be existing ones when applicable (check recent posts for examples)

## Writing Style Guide (Based on Existing Posts)

### Voice and Tone
- Conversational, first-person, confident; explain as a peer.
- Mix technical rigor with light humor and occasional asides.
- Use emoji sparingly but consistently in section headers.
- Consider opening with a short quote or one-liner to set tone.

### Structure and Flow
- Start with a clear framing: problem, constraints, and why it matters.
- Use many H2 sections to chunk the narrative.
- Favor a problem -> options -> decision -> steps -> recap arc.

### CCDD Series Structure
The Claude Code Deep Dive (CCDD) series follows a consistent structure:
1. Hook paragraph (2-4 sentences) + bolded quote + `<!--more-->` + hero image
2. Series index (numbered list linking all previous articles)
3. Content sections with emoji-bookend H2 headers (`## 🔌 Title 🔌`)
4. `## ⏭️ What's Next ⏭️` — bullet list of upcoming series topics
5. `## 🏠 Take Home Points 🏠` — 4-5 concise bullets distilling the post
6. Closing greeting in a foreign language wrapped in flag emoji

### Technical Depth
- Be practical and step-by-step; include tradeoffs and failure modes.
- Use concrete examples, commands, and config snippets.
- Prefer diagrams/screenshots for architecture, workflows, and results.

### Formatting Conventions
- Include `<!--more-->` after the hook/intro.
- Use image assets under the post's `images/` folder.
- Keep headings short; emoji-wrapped headers are a house style.

### Content Cadence Patterns
- Long-form deep dives are common (1.5k+ words).
- Series are encouraged (multi-part explorations of a theme).

### Reference Examples
- Blue/Green Upgrade for Postgres on AWS RDS (tone + diagrams + recap)
- The Art and Science of Kubernetes Bin Packing (depth + visuals)
- Auto Web Login (Parts I-IV) (series structure + step-by-step)

## Deployment

- Automatic on push to `main` branch via GitHub Actions
- Always run `hugo serve` locally to verify before pushing
- CI uses Hugo v0.122.0 (extended)

## Customizations

- `static/custom.css` - site-wide CSS customizations
- `layouts/` - Hugo template overrides
- Theme is a git submodule at `themes/ananke`
- Giscus comments are enabled (configured in `hugo.toml`)
