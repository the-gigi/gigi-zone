# The Gigi Zone

This repo hosts the [Gigi Zone](https://the-gigi.github.io/gigi-zone/) blog. It is generated
by [Hugo](https://gohugo.io/) using
the [Ananke](https://themes.gohugo.io/themes/gohugo-theme-ananke/) theme.

## Usage

To add a new post type (change the year, month and post filename as appropriate):

```
hugo new content content/posts/2024/03/eks-ip-address-assignment.md
```

- Add posts to content/posts/<year>/<month>
- Test locally with `hugo serve`
- Git add, commit and push at will in 'draft' mode
- when you're ready to publish remove the `draft = true` from the front matter

## Bootstrap

This part is here just to keep track of the process in case I want to create another one.

Follow the instructions here:
https://gohugo.io/getting-started/quick-start/

### Hosting on GitHub Pages

THe blog is hosted on GitHub pages.
Check out https://gohugo.io/hosting-and-deployment/hosting-on-github/ 
