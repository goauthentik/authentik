---
title: User logout stage
---

The User Logout stage ends the user's authentik session and, if configured, initiates [Single Logout](../../../providers/single-logout/index.md).

## Overview

This stage removes the current authentik session. When Single Logout is enabled for SAML or OIDC providers, authentik can also inject additional logout handling for those provider sessions.

## Configuration options

This stage has no stage-specific configuration options.

## Flow integration

The default flows use this stage differently:

- `default-invalidation-flow`: used when the user logs out directly from authentik. This flow includes the User Logout stage.
- `default-provider-invalidation-flow`: used when a logout starts from an application. This flow does not include the User Logout stage by default.

Add the User Logout stage to `default-provider-invalidation-flow` if RP-initiated logout should also end the main authentik session.

## Notes

When this stage runs, authentik can inject additional logout stages for active provider sessions:

- front-channel iframe logout stages
- front-channel native logout stages
- back-channel logout execution

This lets provider-specific logout happen automatically without manually adding those stages to the flow.
