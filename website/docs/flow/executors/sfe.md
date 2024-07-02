---
title: Simplified
---

<span class="badge badge--info">authentik 2024.8+</span>

A simplified web-based flow executor which authentik automatically uses for older browsers, which do not support modern web technologies.

Currently this flow executor is automatically used for the following browsers:

-   Internet Explorer
-   Microsoft Edge (up to and including version 18)

The following stages are supported:

-   [**Identification stage**](../stages/identification/)

    :::info
    Only user identifier and user identifier + password stage configurations are supported, sources and passwordless configurations are not supported.
    :::

-   [**Password stage**](../stages/password/)
-   [**Authenticator Validation Stage**](../stages/authenticator_validate/)

Compared to the default flow executor, this flow executor does _not_ support the following features:

-   Localization
-   Theming (Dark / light themes)
-   Theming (Custom CSS)
-   Stages not listed above
-   Flow inspector
