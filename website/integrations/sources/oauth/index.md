---
title: Generic OAuth Source
---

## Generic OAuth Source

:::note
All Integration-specific Sources are documented in the Integrations Section
:::

This source allows users to enroll themselves with an external OAuth-based Identity Provider. The generic provider expects the endpoint to return OpenID-Connect compatible information. Vendor-specific implementations have their own OAuth Source.

-   Policies: Allow/Forbid users from linking their accounts with this provider.
-   Request Token URL: This field is used for OAuth v1 implementations and will be provided by the provider.
-   Authorization URL: This value will be provided by the provider.
-   Access Token URL: This value will be provided by the provider.
-   Profile URL: This URL is called by authentik to retrieve user information upon successful authentication.
-   Consumer key/Consumer secret: These values will be provided by the provider.
