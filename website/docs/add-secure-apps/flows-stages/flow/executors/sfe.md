---
title: Simplified flow executor
authentik_version: "2024.6.1"
---

A simplified web-based flow executor that authentik automatically uses for older browsers that do not support modern web technologies.

Currently this flow executor is automatically used for the following browsers:

- Internet Explorer
- Microsoft Edge (up to and including version 18)

The following stages are supported:

- [**Identification stage**](../../stages/identification/index.mdx)

    :::info
    Only user identifier and user identifier + password stage configurations are supported; sources and passwordless configurations are not supported.
    :::

- [**Password stage**](../../stages/password/index.md)
- [**Authenticator Validation Stage**](../../stages/authenticator_validate/index.mdx)

Compared to the [default flow executor](./if-flow.md), this flow executor does _not_ support the following features:

- Localization
- Theming (Dark / light themes)
- Theming (Custom CSS)
- Stages not listed above
- Flow inspector
