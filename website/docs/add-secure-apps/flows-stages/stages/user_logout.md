---
title: User Logout stage
---

The User Logout stage ends the user's session in authentik and, if configured, triggers [Single Logout (SLO)](../../providers/single-logout/index.md) for [SAML](../../providers/saml/saml_single_logout.md) and [OIDC](../../providers/oauth2/frontchannel_and_backchannel_logout.mdx) providers.

## When the User Logout stage is used

The User Logout stage is included in different default flows depending on how the logout is initiated:

- **`default-invalidation-flow`**: Used when users log out directly from authentik. This flow **includes** the User Logout stage, so the authentik session is ended and Single Logout is triggered for all connected applications.

- **`default-provider-invalidation-flow`**: Used when a user logs out from an application. This flow does **not** include the User Logout stage by default, so only that application's session is ended. The authentik session and other application sessions remain active.

This distinction exists because users may want to sign out of a single application without ending their entire authentik session. To also end the authentik session when users log out from an application, you can add the User Logout stage to the `default-provider-invalidation-flow`. See [Enable full Single Logout for RP-initiated logout](../../providers/single-logout/index.md#enable-full-single-logout-for-rp-initiated-logout) for instructions.

## Logout flow injection

authentik dynamically injects logout stages into the user's current logout flow when provider sessions configured for Single Logout are detected:

1. The `flow_pre_user_logout` signal is triggered before the user is logged out
2. authentik queries for active provider sessions matching the user's authenticated session:
    - **SAML providers**: Queries active SAML sessions for providers with an SLS URL and logout method configured
    - **OIDC providers**: Queries for providers with front-channel or back-channel logout enabled
3. For each logout method with active sessions, the appropriate logout stage is injected:
    - **iframe logout stage**: Injected at index 1 (immediately after the logout stage) for front-channel iframe logout
    - **Native logout stage**: Injected at index 2 (after the iframe logout, if present) for front-channel native logout
    - **Back-channel logout**: Executed server-side without injecting additional stages
4. The user progresses through these injected stages before logout completes

This approach ensures that single logout happens automatically without requiring explicit flow configuration.
