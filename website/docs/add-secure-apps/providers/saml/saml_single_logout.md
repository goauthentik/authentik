---
title: SAML Single Logout
authentik_version: "2025.10.0"
---

[Single Logout (SLO)](../single-logout/index.md) allows authentik to log out users from all configured providers simultaneously when they sign out of authentik. For SAML providers, this requires your service provider to support Single Logout via a Single Logout Service URL. Check your provider's documentation to confirm Single Logout support.

## Configure your SAML provider

To enable single logout, add a **Single Logout Service URL** to your SAML provider. The URL is the service provider’s endpoint to which authentik sends logout requests.

1. Log in to authentik as an administrator and open the authentik Admin interface
2. Navigate to **Applications** > **Providers**
3. Click the edit icon of the SAML provider that you want to configure for SLO
4. Set the **SLS URL** field to your service provider's logout endpoint
5. Select the appropriate **SLS Binding**:
    - **Redirect** - Uses HTTP redirects to send logout requests to the provider (front-channel only)
    - **POST** - Supports both front-channel and back-channel logout methods
6. Select the appropriate **Logout Method**:
    - **Front-channel iframe** - Performs parallel logout requests using hidden iframes. Supports both Redirect and POST bindings
    - **Front-channel native** - Uses the active browser tab to chain redirects and POST requests for sequential logout. Supports both Redirect and POST bindings
    - **Back-channel** - Performs server-to-server POST requests to log out the user. Requires POST SLS binding. Users are logged out even when their session is administratively terminated
7. (Optional) Enable **Sign Logout Request** to cryptographically sign SAML logout requests sent to the service provider
8. Click **Finish**

:::info
Back-channel logout ensures users are logged out even when their session is terminated administratively (e.g., when a user is deactivated or their session is deleted). This requires POST SLS binding.
:::

## How SAML Single Logout Works

When a user logs out of authentik through a logout flow, authentik initiates the single logout process for all SAML providers configured with an SLS URL and logout method.

### Front-channel iframe logout

With front-channel iframe logout, authentik injects an iframe logout stage into the logout flow. This stage loads all provider logout URLs simultaneously in hidden iframes within the browser, allowing parallel logout across multiple providers. After all iframes complete their requests, the user continues through the authentik logout flow.

### Front-channel native logout

With front-channel native logout, authentik chains logout requests sequentially using the active browser tab. For POST bindings, the browser automatically submits forms to each provider. For Redirect bindings, the browser follows redirect URLs. Each provider returns the user to authentik who redirects to the next provider. After all providers have been visited, the user completes the authentik logout flow.

### Back-channel logout

With back-channel logout, authentik sends SAML logout requests directly from the server to each provider's SLS URL via HTTP POST. This happens asynchronously and does not require browser interaction. Back-channel logout is also triggered automatically when:

    - A user's session is administratively deleted.
    - A user account is deactivated.

:::info
Back-channel logout requires POST SLS binding.
:::

## Binding Comparison

| Feature              | Redirect Binding      | POST Binding             |
| -------------------- | --------------------- | ------------------------ |
| Front-channel iframe | ✅ Supported          | ✅ Supported             |
| Front-channel native | ✅ Supported          | ✅ Supported             |
| Back-channel         | ❌ Not supported      | ✅ Supported             |
| Request sent via     | URL query parameters  | HTTP POST body           |
| Maximum data size    | Limited by URL length | Large requests supported |

## SAML session tracking

authentik tracks SAML sessions for each provider to support single logout. When a user successfully authenticates to a SAML provider, authentik creates a `SAMLSession` record containing:

    - The SAML `SessionIndex`
    - The `NameID` and `NameID format` used for the session
    - A link to the user's authenticated session

These session records are used to generate proper SAML logout requests with the correct `SessionIndex` and `NameID` values that the service provider expects.

## Resources

- [Single Logout (SLO) Overview](../single-logout/index.md)
- [User Logout Stage](../../flows-stages/stages/user_logout.md)
- [SAML Profiles 2.0 Specification](https://docs.oasis-open.org/security/saml/v2.0/saml-profiles-2.0-os.pdf)
