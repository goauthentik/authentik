---
title: Docs development environment
sidebar_label: Docs development
tags:
    - development
    - contributor
    - docs
    - docusaurus
---

If you want to only make changes to the documentation, you only need Node.js.

### Prerequisites

- Node.js (any recent version should work; we use 24.x to build)
- Make (again, any recent version should work)

:::info
Depending on platform, some native dependencies might be required. On macOS, run `brew install node@24`
:::

### Instructions

1. Clone the git repo from https://github.com/goauthentik/authentik
2. Run `make docs-install` to install the docs development dependencies
3. Run `make docs-watch` to start a development server to see and preview your changes
4. Finally when you're about to commit your changes, run `make docs` to run the linter and auto-formatter.
