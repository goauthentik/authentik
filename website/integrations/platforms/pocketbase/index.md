---
title: Integrate with PocketBase
sidebar_label: PocketBase
support_level: community
---

## What is PocketBase?

> PocketBase is an open source backend consisting of an embedded SQLite database, realtime subscriptions, built-in auth management, a dashboard UI, and a REST-like API.
>
> -- https://pocketbase.io

## Preparation

The following placeholders are used in this guide:

- `pocketbase.company` is the FQDN of the PocketBase installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of PocketBase with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://pocketbase.company/api/oauth2-redirect`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## PocketBase configuration

1. Sign in to the PocketBase superuser dashboard at `https://pocketbase.company/_/`.
2. If collection controls are locked, navigate to **Settings** > **Application**, disable **Hide/Lock collection and record controls**, and click **Save changes**.
3. Navigate to **Collections** and open the **users** auth collection.
4. Click the gear icon next to the collection name and select the **Options** tab.
5. Open the **OAuth2** section and click **Add provider**.
6. Select **OIDC** and enter the following values:
    - **Client ID**: enter the **Client ID** from authentik.
    - **Client secret**: enter the **Client Secret** from authentik.
    - **Display name**: `authentik`
    - **Auth URL**: `https://authentik.company/application/o/authorize/`
    - **Token URL**: `https://authentik.company/application/o/token/`
    - **User info URL**: `https://authentik.company/application/o/userinfo/`
7. Click **Set provider config**.
8. Click **Save changes**.

## Configuration verification

To confirm that authentik is properly configured with PocketBase, open your application and sign in with the authentik OAuth2 provider.

## Resources

- [PocketBase documentation - Authenticate with OAuth2](https://pocketbase.io/docs/authentication/#authenticate-with-oauth2)
- [PocketBase source - OIDC provider](https://github.com/pocketbase/pocketbase/blob/master/tools/auth/oidc.go)
- [PocketBase source - OAuth2 redirect route](https://github.com/pocketbase/pocketbase/blob/master/apis/record_auth.go)
