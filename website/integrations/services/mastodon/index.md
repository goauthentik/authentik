---
title: Integrate with Mastodon
sidebar_label: Mastodon
---

# Mastodon

<span class="badge badge--secondary">Support level: Community</span>

## What is Mastodon

> Mastodon is free and open-source software for running self-hosted social networking services. It has microblogging features similar to Twitter
>
> -- https://joinmastodon.org/

## Preparation

The following placeholders are used in this guide:

- `mastodon.company` is the FQDN of the mastodon install.
- `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

### Step 1 - OAuth2/OpenID Provider

Create a OAuth2/OpenID Provider (under _Applications/Providers_) with these settings:

- Name : mastodon
- Redirect URI: `https://mastodon.company/auth/auth/openid_connect/callback`

### Step 3 - Application

Create an application (under _Resources/Applications_) with these settings:

- Name: Mastodon
- Slug: mastodon
- Provider: mastodon

## Mastodon Setup

Configure Mastodon `OIDC_` settings by editing the `.env.production` and add the following:

:::warning
When using `preferred_username` as the user identifier, ensure that the [Allow users to change username setting](https://docs.goauthentik.io/docs/sys-mgmt/settings#allow-users-to-change-username) is disabled to prevent authentication issues.
:::

:::info
You can configure Mastodon to use either the `sub` or `preferred_username` as the UID field under `OIDC_UID_FIELD`. The `sub` option uses a unique, stable identifier for the user, while `preferred_username` uses the username configured in authentik.
:::

```
OIDC_ENABLED=true
OIDC_DISPLAY_NAME=authentik
OIDC_DISCOVERY=true
OIDC_ISSUER=< OpenID Configuration Issuer>
OIDC_AUTH_ENDPOINT=https://authentik.company/application/o/authorize/
OIDC_SCOPE=openid,profile,email
OIDC_UID_FIELD=preferred_username
OIDC_CLIENT_ID=<Client ID>
OIDC_CLIENT_SECRET=<Client Secret>
OIDC_REDIRECT_URI=https://mastodon.company/auth/auth/openid_connect/callback
OIDC_SECURITY_ASSUME_EMAIL_IS_VERIFIED=true
```

Restart mastodon-web.service

## Additional Resources

- https://github.com/mastodon/mastodon/pull/16221
- https://forum.fedimins.net/t/sso-fuer-verschiedene-dienste/42
