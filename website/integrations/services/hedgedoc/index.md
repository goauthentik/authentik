---
title: HedgeDoc
---

<span class="badge badge--secondary">Support level: Community</span>

## What is HedgeDoc

> HedgeDoc lets you create real-time collaborative markdown notes.
>
> -- https://github.com/hedgedoc/hedgedoc

## Preparation

The following placeholders will be used:

-   `hedgedoc.company` is the FQDN of the HedgeDoc install.
-   `authentik.company` is the FQDN of the authentik install.

Create an OAuth2/OpenID provider with the following parameters:

-   Client Type: `Confidential`
-   Scopes: OpenID, Email and Profile
-   Signing Key: Select any available key
-   Redirect URIs: `https://hedgedoc.company/auth/oauth2/callback`

Note the Client ID and Client Secret values. Create an application, using the provider you've created above.
To be logged in immediately if you click on the application, set:

-   Launch URL: `https://hedgedoc.company/auth/oauth2`

## HedgeDoc

You need to set the following `env` Variables for Docker based installations.

Set the following values:

```yaml
CMD_OAUTH2_PROVIDERNAME: "authentik"
CMD_OAUTH2_CLIENT_ID: "<Client ID from above>"
CMD_OAUTH2_CLIENT_SECRET: "<Client Secret from above>"
CMD_OAUTH2_SCOPE: "openid email profile"
CMD_OAUTH2_USER_PROFILE_URL: "https://authentik.company/application/o/userinfo/"
CMD_OAUTH2_TOKEN_URL: "https://authentik.company/application/o/token/"
CMD_OAUTH2_AUTHORIZATION_URL: "https://authentik.company/application/o/authorize/"
CMD_OAUTH2_USER_PROFILE_USERNAME_ATTR: "preferred_username"
CMD_OAUTH2_USER_PROFILE_DISPLAY_NAME_ATTR: "name"
CMD_OAUTH2_USER_PROFILE_EMAIL_ATTR: "email"
```
