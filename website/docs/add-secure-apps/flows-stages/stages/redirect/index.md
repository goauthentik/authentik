---
title: Redirect stage
authentik_version: "2024.12"
---

The Redirect stage sends the user either to another flow or to a static URL.

## Overview

This stage is most commonly used to branch from one flow into another while optionally preserving the current flow context.

## Configuration options

- **Keep flow context**: preserve the current flow context when redirecting to another flow.
- **Mode**: choose whether the target is a static URL or another flow.
- **Static target**: URL used in static mode.
- **Target flow**: flow used in flow mode.

## Flow integration

Use this stage when the flow should hand off to another flow or redirect to a fixed destination.

In **flow** mode, the redirected flow can continue using the existing flow context if **Keep flow context** is enabled.

## Notes

- You can override the target dynamically from an expression policy by setting `redirect_stage_target` in the [flow context](../../flow/context/index.mdx#redirect_stage_target-string).
- When **Keep flow context** is disabled, authentik clears the current flow context before handing off, except for the redirect marker used internally to track the redirect.
