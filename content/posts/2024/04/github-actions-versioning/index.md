+++
title = 'Github Actions Versioning'
date = 2024-04-02T00:12:31-07:00
categories = ["DevOps"]
+++

TIL: When using un-pinned versions you must use **@v<major version>**. When using pinned patch
versions use the exact release tag **@<tag>**, which may or may not have a **v** prefix

<!--more-->

Case in point, at work we decided to migrate from un-pinned versions to pinned versions of all our
Github actions.

One of the Github actions we use is:
https://github.com/ravsamhq/notify-slack-action

It's latest release tag at the time of writing is [2.5.0](https://github.com/ravsamhq/notify-slack-action/releases/tag/2.5.0)

Other Github actions like the famous checkout use a release tag like v4.2.1 (note the `v` prefix)

Originally, we used the notify-slack-action using its major version only as in:

```
- uses: ravsamhq/notify-slack-action@2
```

When I pinned the version I changed it to:

```
- uses: ravsamhq/notify-slack-action@v2.5.0 
```

That resulted in the error:

```
Prepare all required actions
Getting action download info
Error: Unable to resolve action `ravsamhq/notify-slack-action@v2.5.0`, unable to find version `v2.5.0`
```

The corresponding change to actions/checkout worked like a charm:

```
actions/checkout@v4 -> actions/checkout@v4.1.2
```

I was a little surprised, but then I check the actual release tags and noticed the discrepancy where
actions/checkout includes the v prefix in its tags.

The fix was simply to drop the v prefix from the pinned version of ravsamhq/notify-slack-actio:

```
uses: ravsamhq/notify-slack-action@2.5.0
```

This inconsistency of using the **v** prefix between pinned and un-pinned version is pretty odd.

![](shrugging-octocat.png)
