---
title: Integrate with Mastodon
sidebar_label: Mastodon
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Mastodon?

> Mastodon is free and open-source software for running self-hosted social networking services. It has microblogging features similar to Twitter.
>
> -- https://joinmastodon.org/

## Preparation

The following placeholders are used in this guide:

- `mastodon.company` is the FQDN of the Mastodon installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Mastodon with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because you will use it later as `<application_slug>`.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://mastodon.company/auth/auth/openid_connect/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Mastodon configuration

Configure Mastodon's `OIDC_` settings by editing `.env.production` and adding the following values:

```env title=".env.production"
OIDC_ENABLED=true
OIDC_DISPLAY_NAME=authentik
OIDC_DISCOVERY=true
OIDC_ISSUER=https://authentik.company/application/o/<application_slug>/
OIDC_SCOPE=openid,profile,email
OIDC_UID_FIELD=preferred_username
OIDC_CLIENT_ID=<Client ID from authentik>
OIDC_CLIENT_SECRET=<Client Secret from authentik>
OIDC_REDIRECT_URI=https://mastodon.company/auth/auth/openid_connect/callback
OIDC_SECURITY_ASSUME_EMAIL_IS_VERIFIED=true
```

:::warning Stable Mastodon usernames
This configuration uses the authentik `preferred_username` claim as the Mastodon user identifier so that new Mastodon usernames match authentik usernames. Disable the [**Allow users to change username** setting](/docs/sys-mgmt/settings#allow-users-to-change-username) in authentik to prevent authentication issues after username changes.
:::

Alternatively, you can set `OIDC_UID_FIELD=sub` to use authentik's stable subject identifier instead of the username.

Restart the Mastodon web service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Mastodon, open Mastodon and log in using the **authentik** login option.

## Resources

- [Mastodon documentation - Configuring your environment](https://docs.joinmastodon.org/admin/config/#external-authentication)
- [Mastodon source - OmniAuth initializer](https://github.com/mastodon/mastodon/blob/main/config/initializers/3_omniauth.rb)
- [Mastodon source - authentication routes](https://github.com/mastodon/mastodon/blob/main/config/routes.rb)
