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

## Deployment

- Automatic on push to `main` branch via GitHub Actions
- Always run `hugo serve` locally to verify before pushing
- CI uses Hugo v0.122.0 (extended)

## Customizations

- `static/custom.css` - site-wide CSS customizations
- `layouts/` - Hugo template overrides
- Theme is a git submodule at `themes/ananke`
- Giscus comments are enabled (configured in `hugo.toml`)
