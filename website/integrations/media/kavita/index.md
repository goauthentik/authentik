---
title: Integrate with Kavita
sidebar_label: Kavita
support_level: community
---

## What is Kavita?

> Kavita is a self-hosted digital library and reading server for manga, comics, books, and other digital media, with support for organizing collections and reading in the browser.
>
> -- https://www.kavitareader.com/

## Preparation

The following placeholders are used in this guide:

- `kavita.company` is the FQDN of the Kavita installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Kavita with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://kavita.company/signin-oidc`
        - Add a **Redirect URI** of type `Strict` `Post Logout` as `https://kavita.company/signout-callback-oidc`
          **Logout URI**: `https://kavita.company/signout-oidc`
          **Logout Method**: `Front-channel`
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Kavita configuration

1. Log in to Kavita as an administrator.
2. Navigate to **Settings** > **OpenID Connect**.
3. Configure the following settings:
    - **Authority**: `https://authentik.company/application/o/<application_slug>/`
    - **Client Id**: enter the Client ID from authentik.
    - **Secret**: enter the Client Secret from authentik.
    - **Provision Accounts**: enable this setting to automatically create Kavita accounts for users who log in through authentik.
    - **Require Verified Emails**: disable this setting.
4. Click **Save**.

You must restart your Kavita instance for these changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Kavita, log out of Kavita and then log back in using the **Login with SSO** option. You should be redirected to authentik for authentication and then redirected back to Kavita as a logged-in user.

## Resources

- [Kavita OpenID Connect documentation](https://wiki.kavitareader.com/guides/admin-settings/open-id-connect/)
