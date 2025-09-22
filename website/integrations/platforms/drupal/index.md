---
title: Integrate with Drupal
sidebar_label: Drupal
support_level: community
---

## What is Drupal

> Drupal is a free and open-source content management system written in PHP and
> paired with a database.
>
> -- https://en.wikipedia.org/wiki/Drupal

## Preparation

The following placeholders are used in this guide:

- `drupal.company` is the FQDN of the Drupal installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::note
There are many different modules for Drupal that allow you to set up SSO using different authentication methods. This tutorial uses the [OpenID Connect / OAuth client](https://www.drupal.org/project/openid_connect) module.
:::

## authentik configuration

To support the integration of Drupal with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. The **slug** will be used in URLs and should match the `drupal-slug` placeholder defined earlier.
- **Choose a Provider type**: select **OAuth2/OpenID Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), and configure the following required settings:
    - Add the following **Redirect URI**: `https://drupal.company/openid-connect/generic`
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.
4. Note the **Client ID** and **Client Secret** for later use.

## Drupal configuration

1. From the Admin Toolbar or admin page at `https://drupal.company/admin`, navigate to **Configuration** > **Web Services** > **OpenID Connect** (or directly at `https://drupal.company/admin/config/services/openid-connect`)
2. Configure the following settings:
    - Set the **Client ID** and **Client Secret** to the values noted from authentik
    - Configure the endpoints:
        - **Authorization endpoint**: `https://authentik.company/application/o/authorize/`
        - **Token endpoint**: `https://authentik.company/application/o/token/`
        - **UserInfo endpoint**: `https://authentik.company/application/o/userinfo/`
3. Under **Admin** > **Configuration** > **People** > **Account Settings** (or `https://drupal.company/admin/config/people/accounts`):
    - If new user registration is disabled, check **Override registration settings** to enable new account creation
    - Note: Without this setting, new users will receive a message that their account is blocked pending administrator approval
4. Enable the OpenID button on the user login form

:::info
If you are developing Drupal locally with DDEV and authentik is also running locally, use `host.docker.internal:9000` as the hostname for the Token and UserInfo endpoints.
:::

## Configuration verification

TODO

## Additional Resources

- [Drupal OpenID Connect Module Documentation](https://www.drupal.org/project/openid_connect)
- [Drupal User Account Settings Documentation](https://www.drupal.org/docs/user_guide/en/user-registration.html)
