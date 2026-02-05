---
title: Single Logout (SLO)
authentik_version: "2025.10.0"
---

Single Logout (SLO) is a security feature that logs users out of all active applications when they log out of authentik. It uses the OAuth2/OpenID Connect front-channel and back-channel logout specifications in combination with SAML's Single Logout specification.

For example, if a user is concurrently logged into an OIDC application and two SAML applications, when the user logs out of authentik, they will automatically be logged out of all three applications. Without SLO configured, users with active sessions across multiple applications would need to manually log out of each one.

:::info
Check with your service provider to see if they support SAML Single Logout or OIDC front-channel/back-channel logout. Not all service providers support these features.
:::

## When Single Logout is triggered

Single Logout behavior depends on where the user initiates logout:

- **Logout from authentik**: When users log out directly from authentik, the `default-invalidation-flow` runs. This flow includes a [User Logout stage](../../flows-stages/stages/user_logout.md) that ends the authentik session and triggers Single Logout for all connected applications.

- **Logout from an application**: When users log out from an OIDC or SAML application, the `default-provider-invalidation-flow` runs. By default, this flow does **not** include a User Logout stage, so only that application's session is ended while the authentik session and other application sessions remain active.

To enable full Single Logout when users log out from an application, see [Enable full Single Logout for RP-initiated logout](#enable-full-single-logout-for-rp-initiated-logout) below.

## How Single Logout works in authentik

When a user logs out or their session is terminated in authentik, the following process occurs:

1. **Session Termination**: The user's session ends through one of the following:
    - User-initiated logout via a logout flow
    - Administrative action (session deletion or user deactivation)
    - Token revocation or expiration
2. **Provider Identification**: authentik identifies all OAuth2/OIDC and SAML providers with active sessions for the users who have SLO configured.
3. **Logout Request Dispatch**:
    - **Back-channel**: HTTP POST requests are sent directly from the authentik server to each back-channel provider's configured logout endpoint.
    - **Front-channel**: For user-initiated logouts, a logout stage is automatically injected into the flow that handles browser-based logout (typically via iframes or sequential redirects).
4. **Provider Processing**: Each provider processes the logout request, validates it, and terminates the user's active session.
5. **Completion**: After all providers have been notified, the user is redirected back to the authentik login screen.

## Front-channel vs. back-channel logout

authentik supports both front-channel (browser-based) and back-channel (server-to-server) logout methods, depending on how each provider is configured.

### Front-channel logout

Front-channel logout sends logout requests through the user's browser. authentik supports two front-channel modes:

#### iframe mode (default for OIDC)

    - Loads all provider logout URLs simultaneously in hidden iframes
    - Provides fast, parallel logout across multiple providers
    - Required by the OIDC front-channel logout specification
    - Most SAML providers also support iframe-based logout

#### Native Mode (SAML Only)

    - Uses the active browser tab to chain redirects and POST requests sequentially
    - Provides better compatibility with SAML providers that have iframe restrictions
    - Each provider redirects the user back to authentik before proceeding to the next provider
    - Not available for OIDC providers as the specification requires iframe support

:::info
Use native front-channel mode for SAML providers if you encounter iframe compatibility issues, such as Content Security Policy (CSP) restrictions or cookie handling problems.
:::

### Back-channel Logout

Back-channel logout sends logout requests directly from the authentik server to each provider's logout endpoint via HTTP POST.

    - Does not require user browser interaction
    - Works even when the user is offline or their browser is closed
    - Is automatically triggered by administrators terminating a user session (user deactivation or session deletion)
    - Requires the provider to accept server-to-server POST requests

**For SAML**: Requires POST SLS binding.
**For OIDC**: Requires a `logout_uri` configured for back-channel that accepts logout tokens.

## Enable RP-initiated Single Logout

By default, when a user logs out from an application (RP-initiated logout), only that application's session is ended. To enable full Single Logout that also ends the user's authentik session and logs them out of all applications, add a User Logout stage to the `default-provider-invalidation-flow`:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. Click `default-provider-invalidation-flow` to open the flow.
4. Click the **Stage Bindings** tab.
5. Click **Bind Existing Stage**.
6. In the **Stage** dropdown, select `default-invalidation-logout`.
7. Click **Create**.

After this change, when users log out from any application, they will be logged out of authentik and all other connected applications.

## Configure per-provider logout behavior

If you need different logout behaviors for different applications, you can create custom invalidation flows and assign them to specific providers:

1. Create a new flow with the **Invalidation** designation.
2. Add stages as needed:
    - Include a [User Logout stage](../../flows-stages/stages/user_logout.md) if you want full Single Logout.
    - Omit the User Logout stage if you only want to end the specific application session.
3. When configuring a provider, select your custom flow in the **Invalidation flow** field.

This allows you to configure full Single Logout only for sensitive applications while keeping the default behavior for others.

## Enable Single Logout

Enabling single logout requires configuring logout endpoints on your SAML or OIDC providers in authentik.

### SAML Providers

See the [SAML Single Logout documentation](../saml/saml_single_logout.md) for detailed instructions. You will need to:

1. Configure the **SLS URL** (Single Logout Service URL) - the provider's logout endpoint
2. Select the **SLS Binding** (Redirect or POST)
3. Choose a **Logout Method**; front-channel iframe, front-channel native, or back-channel
4. Optionally, enable **Sign Logout Request** for additional security

### OIDC providers

See the [OIDC Front-channel and Back-channel logout documentation](../oauth2/frontchannel_and_backchannel_logout.mdx) for detailed instructions. You will need to:

1. Configure the **logout URI** - the provider's logout endpoint
2. Enable the desired **Logout Method**; front-channel or back-channel
3. Optionally configure logout token signing for back-channel requests

## Session tracking

authentik tracks provider sessions to enable single logout:

    - **SAML**: Creates `SAMLSession` records containing the `SessionIndex`, `NameID`, and `NameID format` for each successful authentication.
    - **OIDC**: Tracks session identifiers (`sid`) and ID tokens required for logout requests.

These session records are automatically created during authentication and deleted after logout or expiration.

## Administrative session termination

Back-channel logout is always triggered when a user session is terminated via administrative actions:

    - **Session Deletion**: When an administrator manually deletes a user's session through the Admin interface or API, authentik sends back-channel logout requests to all configured providers.
    - **User Deactivation**: When a user account is deactivated, authentik automatically sends back-channel logout requests to terminate all active sessions across all providers.

These requests are processed asynchronously to avoid blocking administrative operations.

## Resources

- [SAML Single Logout](../saml/saml_single_logout.md)
- [OIDC Front-channel and Back-channel Logout](../oauth2/frontchannel_and_backchannel_logout.mdx)
- [User Logout Stage](../../flows-stages/stages/user_logout.md)
- [SAML Profiles 2.0 Specification](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf)
- [OpenID Connect Front-Channel Logout 1.0](https://openid.net/specs/openid-connect-frontchannel-1_0.html)
- [OpenID Connect Back-Channel Logout 1.0](https://openid.net/specs/openid-connect-backchannel-1_0.html)
