---
title: Integrate with PocketBase
sidebar_label: PocketBase
support_level: community
---

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

To support the integration of Pocketbase with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://pocketbase.company/api/oauth2-redirect`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## PocketBase configuration

1. Sign in to PocketBase and access the superusers dashboard by navigating to `https://pocketbase.company/\_/#/settings`.
2. Toggle off **Hide collection create and edit controls**," then click the **Save changes** button.
3. Open the **users** collection by clicking the **Collections** icon on the sidebar or head to `https://pocketbase.company/\_/#/collections?collection=pb_users_auth`.
4. Click the gear icon next to the collection's name, then select the **Options** tab in the popup on the right.
5. Enable the **OAuth2** authentication method by clicking the **OAuth2** tab and toggling **Enable**.
6. Click **+ Add provider**, then select **OpenID Connect**.
7. Enter the following details from the authentik provider:
    - Set **Client ID** to the Client ID copied from authentik.
    - Set **Client secret** to the Client Secret copied from authentik.
    - Set **Display name** to `authentik`.
    - Set **Auth URL** to `https://authentik.company/application/o/authorize/`.
    - Set **Token URL** to `https://authentik.company/application/o/token/`.
    - Make sure **Fetch user info from** is set to `User info URL`, then set **User info URL** to `https://authentik.company/application/o/userinfo/`
