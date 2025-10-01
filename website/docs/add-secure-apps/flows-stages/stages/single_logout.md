---
title: Single Logout (SLO)
---

Single Logout is a security feature that logs a user out of all their applications with active sessions when they log out of authentik. It uses the OAuth2/OpenID Connect front-channel and back-channel logout specifications in combination with SAML's Single Logout specification.

For example, if a user is concurrently logged into one OIDC provider and two SAML providers, when the user logs out of authentik, they will automatically be logged out of all three applications. Without SLO configured, users with active sessions across multiple providers would need to manually log out of each one individually.

:::info
Check with your service provider to see if they support SAML Single Logout or OIDC front-channel/back-channel logout. Not all providers support these features.
:::

## How Single Logout works in authentik

When a user logs out or their session is terminated in authentik, the following process occurs:

1. **Session Termination**: The user's session ends through one of the following:
    - User-initiated logout via a logout flow.
    - Administrative action (session deletion or user deactivation).
    - Token revocation or expiration.
2. **Provider Identification**: authentik identifies all OAuth2/OIDC and SAML providers with active sessions for the user that have SLO configured.
3. **Logout Request Dispatch**:
    - **Back-channel**: HTTP POST requests are sent directly from the authentik server to each back-channel provider's configured logout endpoint.
    - **Front-channel**: For user-initiated logouts, a logout stage is automatically injected into the flow that handles browser-based logout (typically via iframes or sequential redirects).
4. **Provider Processing**: Each provider processes the logout request, validates it, and terminates the user's active session.
5. **Completion**: Once all providers have been notified, the user's authentik session is fully terminated and they are redirected accordingly.

## Front-Channel vs. Back-Channel Logout

authentik supports both front-channel (browser-based) and back-channel (server-to-server) logout methods, depending on how each provider is configured.

### Front-Channel Logout

Front-channel logout sends logout requests through the user's browser. authentik supports two front-channel modes:

#### iframe Mode (Default for OIDC)

- Loads all provider logout URLs simultaneously in hidden iframes.
- Provides fast, parallel logout across multiple providers.
- Required by the OIDC front-channel logout specification.
- Most SAML providers also support iframe-based logout.
- Provides fast, parallel logout across multiple providers
- Required by the OIDC front-channel logout specification
- Most SAML providers also support iframe-based logout

#### Native Mode (SAML Only)

- Uses the active browser tab to chain redirects and POST requests sequentially.
- Provides better compatibility with SAML providers that have iframe restrictions.
- Each provider redirects the user back to authentik before proceeding to the next provider.
- Not available for OIDC providers as the specification requires iframe support.

:::info
Use native front-channel mode for SAML providers if you encounter iframe compatibility issues, such as Content Security Policy (CSP) restrictions or cookie handling problems.
:::

### Back-Channel Logout

Back-channel logout sends logout requests directly from the authentik server to the provider's logout endpoint via HTTP POST.

- Does not require user browser interaction.
- Works even when the user is offline or their browser is closed.
- Is automatically triggered by administrators terminating a user session (user deactivation or session deletion).
- Requires the provider to accept server-to-server POST requests.

**For SAML**: Requires POST SLS binding.
**For OIDC**: Requires a `logout_uri` configured for back-channel that accepts logout tokens.

## Enable Single Logout

Enabling single logout requires configuring logout endpoints on your SAML or OIDC providers in authentik.

### SAML Providers

See the [SAML Single Logout documentation](../../providers/saml/saml_single_logout.md) for detailed instructions. You will need to:

1. Configure the SLS URL (Single Logout Service URL) - the provider's logout endpoint.
2. Select the SLS Binding (Redirect or POST).
3. Choose a Logout Method; front-channel iframe, front-channel native, or back-channel.
4. Optionally, enable `Sign logout request` for additional security.

### OIDC Providers

See the [OIDC Front-channel and Back-channel Logout documentation](../../providers/oauth2/fontchannel_and_backchannel_logout.mdx) for detailed instructions. You will need to:

1. Configure logout URLs:
    - Front-channel logout URL - the provider's front-channel logout endpoint (typically end_session_endpoint).
    - Back-channel logout URL - the provider's back-channel logout endpoint (typically backchannel_logout_uri).
2. Enable the desired logout method; front-channel, back-channel, or both.
3. Optionally configure logout token signing for back-channel requests.

## Session tracking

authentik tracks provider sessions to enable single logout:

- **SAML**: Creates `SAMLSession` records containing the `SessionIndex`, `NameID`, and `NameID format` for each successful authentication.
- **OIDC**: Tracks session identifiers (`sid`) and ID tokens required for logout requests.

These session records are automatically created during authentication and cleaned up after logout or expiration.

## Administrative session termination

Back-channel logout is triggered even when a user session is terminated via administrative actions:

- **Session Deletion**: When an administrator manually deletes a user's session through the Admin interface or API, authentik sends back-channel logout requests to all configured providers.
- **User Deactivation**: When a user account is deactivated, authentik automatically sends back-channel logout requests to terminate all active sessions across all providers.

These requests are processed asynchronously to avoid blocking administrative operations.

## Resources

- [SAML Single Logout](../../providers/saml/saml_single_logout.md)
- [OIDC Front-channel and Back-channel Logout](../../providers/oauth2/fontchannel_and_backchannel_logout.mdx)
- [User Logout Stage](./user_logout.md)
- [SAML Profiles 2.0 Specification](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf)
- [OpenID Connect Front-Channel Logout 1.0](https://openid.net/specs/openid-connect-frontchannel-1_0.html)
- [OpenID Connect Back-Channel Logout 1.0](https://openid.net/specs/openid-connect-backchannel-1_0.html)
