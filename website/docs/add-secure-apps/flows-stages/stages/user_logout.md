---
title: User logout stage
---

The User Logout stage terminates the user's session in authentik and, for configured service providers, triggers Single Logout (SLO).

## Provider logout integration

When users have authenticated to external applications through authentik, the User Logout stage automatically logs them out of those applications. This is supported for:

- **SAML providers** - [Single Logout (SLO) support](../../providers/saml/IDP-initiated-single-logout.md)
- **OAuth2/OIDC providers** - [Backchannel logout support](../../providers/oauth2/backchannel-logout.mdx)

OIDC providers use back-channel logout and require no additional configuration to the User Logout stage. SAML providers may use front-channel logout, which can be configured in the User Logout stage.

## SAML front-channel logout

The User Logout stage supports two front-channel logout modes for SAML providers:

- **Iframe-based front-channel logout** (default) - Performs parallel logout requests using hidden iframes
- **Redirect-based front-channel logout** - Sequential logout using browser redirects (legacy)

To use the sequential redirect method instead, enable **Redirect based SAML Single Logout** in the User Logout stage settings.

## Enabling SAML Single Logout

To enable SAML Single Logout, add an SLS endpoint to your [SAML Provider](../../providers/saml/index.md#single-logout-service-url) configuration.
