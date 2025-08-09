---
title: SAML IDP Initiated Single Logout
description: Configure SAML IDP Initiated Single Logout for SAML Providers
authentik_version: "2025.8.0"
---

authentik supports SAML IDP Initiated Single Logout (SLO), which allows users to log out of authentik and all connected SAML service providers simultaneously.
In order to use this feature, you must set a [Single Logout Service URL](./index.md#single-logout-service-url) in your SAML Provider settings.

## Logout Methods

When users log out of authentik, they are automatically logged out of all SAML service providers accessed during their session. authentik supports three logout methods:

- **Iframe-based front-channel logout** (default) - Performs parallel logout requests using hidden iframes
- **Redirect-based front-channel logout** - Sequential logout using browser redirects (legacy)
- **Back-channel logout** - Server-to-server POST requests without user interaction

:::info
Front-channel logouts occur in the user's browser, while back-channel logouts happen directly between servers and work even when sessions are terminated administratively.
:::

### Logout Stage Configuration

The front-channel logout behavior is controlled by the [User Logout stage](../../flows-stages/stages/user_logout.md) in your logout flow. By default, authentik uses iframes for efficient parallel logout. To switch to the legacy sequential redirect method:

1. Navigate to **Flows & Stages** → **Stages**
2. Edit your **User Logout** stage
3. Enable **Redirect based SAML Single Logout**
