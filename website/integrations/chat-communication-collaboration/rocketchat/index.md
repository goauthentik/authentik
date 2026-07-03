---
title: Integrate with Rocket.Chat
sidebar_label: Rocket.Chat
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Rocket.Chat?

> Centralize real-time messaging, voice, video, AI, and apps for secure, reliable and unified communication among internal and external stakeholders.
>
> -- https://www.rocket.chat/

## Preparation

The following placeholders are used in this guide:

- `rocket.company` is the FQDN of the Rocket.Chat installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Rocket.Chat with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://rocket.company/_oauth/authentik`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Rocket.Chat configuration

This guide uses `authentik` as the Rocket.Chat custom OAuth name. If you choose a different name, update the redirect URI in authentik to match the callback URL shown by Rocket.Chat.

1. Log in to Rocket.Chat as a system administrator.
2. Navigate to **Manage** > **Workspace** > **Settings** > **OAuth**.
3. Click **Add custom OAuth**, enter `authentik` as the unique name, and click **Add**.
4. Open the new custom OAuth configuration and configure the following settings:
    - **Enable**: turn the switch on.
    - **URL**: `https://authentik.company/application/o`
    - **Token Path**: `/token/`
    - **Identity Path**: `/userinfo/`
    - **Authorize Path**: `/authorize/`
    - **Scope**: `openid email profile`
    - **Id**: the Client ID from authentik
    - **Secret**: the Client Secret from authentik
    - **Login Style**: `Redirect`
    - **Button Text**: `Login with authentik`
    - **Username field**: `preferred_username`
    - **Email field**: `email`
    - **Name field**: `name`

5. Click **Save changes**.
6. Click **Refresh OAuth Services**.

To link existing Rocket.Chat users to authentik identities with matching usernames, enable **Merge users** before users sign in with authentik.

### Optional account settings

Navigate to **Manage** > **Workspace** > **Settings** > **Accounts** and disable the following settings:

- **Allow Name Change**
- **Allow Username Change**
- **Allow Email Change**
- **Allow Password Change for OAuth Users**

If authentik handles multi-factor authentication, review **Accounts** > **Two Factor Authentication** and avoid enabling Rocket.Chat two-factor authentication for OAuth users unless you want them to complete an additional challenge after returning from authentik.

To prevent password self-registration, navigate to **Accounts** > **Registration** and set **Registration Form** to **Disabled**.

## Configuration verification

To confirm that authentik is properly configured with Rocket.Chat, log out of Rocket.Chat and log back in using **Login with authentik**.

## Resources

- [Rocket.Chat Custom OAuth Setup](https://docs.rocket.chat/docs/custom-oauth-setup)
- [Rocket.Chat Accounts Settings](https://docs.rocket.chat/docs/accounts)
- [Rocket.Chat Two Factor Authentication Configuration](https://docs.rocket.chat/docs/two-factor-authentication-configuration)
