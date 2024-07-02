---
title: Outline
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Outline

> Outline is a knowledge management platform designed to help teams organize their documentation and streamline access to information.
>
> -- https://www.getoutline.com

## Preparation

The following placeholders will be used:

-   `outline.company` is the FQDN of the Outline install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik configuration

1. Create an OAuth2/OpenID provider with the following parameters:

-   Client Type: `Confidential`
-   Scopes: OpenID, Email and Profile
-   Signing Key: Select any available key
-   Redirect URIs: `https://outline.company/auth/oidc.callback`

2. Note the Client ID and Client Secret values.

## Outline configuration

You need to set the following `env` variables for Docker-based installations.

1. Set the following values:

```yaml
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_AUTH_URI=https://authentik.company/application/o/authorize/
OIDC_TOKEN_URI=https://authentik.company/application/o/token/
OIDC_USERINFO_URI=https://authentik.company/application/o/userinfo/
OIDC_LOGOUT_URI=https://authentik.company/application/o/wiki/end-session/
OIDC_USERNAME_CLAIM=preferred_username
OIDC_DISPLAY_NAME=authentik
OIDC_SCOPES=openid profile email
```
