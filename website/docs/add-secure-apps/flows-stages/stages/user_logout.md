---
title: User Logout stage
---

The User Logout stage terminates the user's session in authentik and, if configured, triggers [Single Logout](./single_logout.md) in [SAML](../../providers/saml/saml_single_logout.md) and [OIDC](../../providers/oauth2/fontchannel_and_backchannel_logout.mdx) providers.

## Logout flow injection

authentik dynamically injects logout stages into the user logout flow when provider sessions requiring logout are detected:

1. The `flow_pre_user_logout` signal is triggered before the user is logged out.
2. authentik queries for active provider sessions matching the user's authenticated session:
    - **SAML providers**: Queries active SAML sessions for providers with an SLS URL and logout method configured.
    - **OIDC providers**: Queries for providers with front-channel or back-channel logout enabled.
3. For each logout method with active sessions, the appropriate logout stage is injected:
    - **iframe logout stage** - Injected at index 1 (immediately after the logout stage) for front-channel iframe logout.
    - **Native logout stage** - Injected at index 2 (after iframe logout, if present) for front-channel native logout.
    - **Back-channel logout** - Executed server-side without injecting additional stages.
4. The user progresses through these injected stages before logout completes.

This approach ensures that single logout happens automatically without requiring explicit flow configuration.

## Administrative session termination

Back-channel logout provides robust session management for administrative scenarios:

- **Session deletion**: When an administrator deletes a user's authenticated session (e.g., via the Admin interface or API), authentik automatically sends back-channel logout requests to all providers configured for back-channel logout.
- **User deactivation**: When a user account is deactivated, authentik sends back-channel logout requests to terminate all active sessions for that user across all providers.

These logout requests are sent asynchronously using background tasks, ensuring they don't block the administrative action.
