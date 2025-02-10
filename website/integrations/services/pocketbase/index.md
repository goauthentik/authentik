---
title: Integrate with PocketBase
sidebar_label: PocketBase
---

# Integrate With PocketBase

<span class="badge badge--secondary">Support level: Community</span>

## What is PocketBase

> PocketBase is a lightweight backend solution that provides a built-in database, authentication, and file storage.
> It allows developers to quickly set up and manage backend services without complex configurations.
> With its simple API and easy-to-use dashboard, it's perfect for small projects, prototypes, or even full-scale applications.
>
> -- https://pocketbase.io/

:::note
If your application relies on PocketBase as its backend, you may need to replace the pocketbase.company placeholder with your application's name.
However, if PocketBase is hosted on a separate domain and users are redirected there for authentication, this notice may not be necessary. Conversely, if PocketBase is hosted on the same domain as your application, this distinction might be relevant.
:::

## Preparation

The following placeholders are used in this guide:

- `pocketbase.company` is the FQDN of the PocketBase installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

[Create](https://docs.goauthentik.io/docs/add-secure-apps/applications/manage_apps#add-new-applications) an OAuth2/OpenID provider and an application in authentik. Use the following parameters for the OAuth2/OpenID provider:

1. In the authentik Admin interface, navigate to **Applications** -> **Applications**.
2. Use the wizard to create a new application and provider. During this process:
    - Note the **Client ID**, **Client Secret**, and **slug** values for later use.
    - Select implicit or explicit authorization flow as desired.
    - Set the redirect URI to <kbd>https://<em>pocketbase.company</em>/api/oauth2-redirect</kbd>.
    - Select any available signing key.

## PocketBase configuration

1. Sign in to PocketBase and access the superusers dashboard by navigating to <kbd>https://<em>pocketbase.company</em>/\_/#/settings</kbd>.
2. Toggle off **Hide collection create and edit controls**," then click the **Save changes** button.
3. Open the **users** collection by clicking the **Collections** icon on the sidebar or head to <kbd>https://<em>pocketbase.company</em>/\_/#/collections?collection=pb_users_auth</kbd>.
4. Click the gear icon next to the collection's name, then select the **Options** tab in the popup on the right.
5. Enable the **OAuth2** authentication method by clicking the **OAuth2** tab and toggling **Enable**.
6. Click **+ Add provider**, then select **OpenID Connect**.
7. Enter the following details from the authentik provider:
    - Set **Client ID** to the Client ID copied from authentik.
    - Set **Client secret** to the Client Secret copied from authentik.
    - Set **Display name** to `authentik`.
    - Set **Auth URL** to <kbd>https://<em>authentik.company</em>/application/o/authorize/</kbd>.
    - Set **Token URL** to <kbd>https://<em>authentik.company</em>/application/o/token/</kbd>.
    - Make sure **Fetch user info from** is set to `User info URL`, then set **User info URL** to <kbd>https://<em>authentik.company</em>/application/o/userinfo/</kbd>
