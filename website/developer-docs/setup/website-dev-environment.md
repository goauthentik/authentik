---
title: Website development environment
---

If you want to only make changes to the website, you only need node.

### Prerequisites

-   Node.js (any recent version should work; we use 20.x to build)
-   Make (again, any recent version should work)

:::info
Depending on platform, some native dependencies might be required. On macOS, run `brew install node@20`
:::

### Instructions

1. Clone the git repo from https://github.com/goauthentik/authentik
2. Run `make website-install` to install the website development dependencies
3. Run `make website-watch` to start a development server to see and preview your changes
4. Finally when you're about to commit your changes, run `make website` to run the linter and auto-formatter.
