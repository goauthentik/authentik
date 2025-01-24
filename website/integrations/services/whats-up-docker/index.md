---
title: Integrate with What's Up Docker
sidebar_label: What's Up Docker
---

# Integrate with What's Up Docker

<span class="badge badge--secondary">Support level: Community</span>

## What is What's Up Docker

> What's Up Docker (WUD) is an easy-to-use tool that alerts you whenever a new version of your Docker containers is released.
>
> -- https://getwud.github.io/wud/

## Preparation

The following placeholders are used in this guide:

- `wud.company` is the FQDN of the WUD installation.
- `authentik.company` is the FQDN of the authentik installation.

## WUD configuration

To configure WUD to use authentik, add the following values to your `.env` file:

```
WUD_AUTH_OIDC_AUTHENTIK_CLIENTID=<Your Client ID>
WUD_AUTH_OIDC_AUTHENTIK_CLIENTSECRET=<Your Client Secret>
WUD_AUTH_OIDC_AUTHENTIK_DISCOVERY=https://authentik.company/application/o/wud/.well-known/openid-configuration
WUD_AUTH_OIDC_AUTHENTIK_REDIRECT=true # Set to true to skip internal login page
```

After making these changes, restart your Docker containers to apply the new configuration.

## authentik configuration

1. Access the **Admin Interface** in on your authentik installation.
2. Create a new **OAuth2 / OpenID Provider**.
3. Note the generated **Client ID** and **Client Secret**.
4. In the provider settings, add this redirect URL under **Redirect URIs/Origins (RegEx)**: `https://wud.company/auth/oidc/authentik/cb`
5. Ensure the `email`, `openid`, and `profile` scopes are selected under **Advanced protocol settings**.
6. Click **Finish** to save the provider configuration.
7. Create a new application associated with this provider.

Once completed, What's Up Docker should be successfully configured to use authentik as its Single Sign-On SSO provider.
