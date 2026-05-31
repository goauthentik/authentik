---
title: Integrate with Icinga Web 2
sidebar_label: Icinga Web 2
support_level: community
---

## What is Icinga Web 2?

> Icinga Web 2 is the next-generation web interface for the Icinga monitoring stack. It provides a flexible UI to view monitoring states, drill into problems, and integrate with the Icinga 2 backend.
>
> -- https://icinga.com/

This guide was tested with Icinga Web 2 2.13, the third-party [RISE-GmbH OIDC module for Icinga Web 2](https://github.com/RISE-GmbH/icingaweb2-module-oidc) 0.7.6, and authentik 2026.5.2.

## Preparation

The following placeholders are used in this guide:

- `icinga.company` is the FQDN of the Icinga Web 2 installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This guide assumes the `oidc` module from RISE-GmbH is already installed, enabled, and configured with a database resource. Refer to the [module installation documentation](https://github.com/RISE-GmbH/icingaweb2-module-oidc/blob/main/doc/02-Installation.md) for the prerequisites.
:::

The redirect URI that the OIDC module expects is constructed from the **Name** you give the provider on the Icinga side: `https://icinga.company/icingaweb2/oidc/authentication/realm?name=<provider-name>`. Decide on this name before you create the authentik provider, because you need to register the matching redirect URI in authentik. This guide uses `authentik` as the provider name.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Icinga Web 2 with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because you will use it when configuring Icinga Web 2.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Set a `Strict` redirect URI to `https://icinga.company/icingaweb2/oidc/authentication/realm?name=authentik` (replace `authentik` with the provider name you choose for the Icinga side, if different).
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Icinga Web 2 configuration

1. Log in to Icinga Web 2 as an administrator.
2. Open the OIDC module and click **New Provider**.
3. Configure the following fields:
    - **Name**: `authentik` (must match the value of the `name` query parameter in the redirect URI you registered in authentik).
    - **Url**: `https://authentik.company/application/o/<application_slug>/`
    - **Secret**: the Client Secret from the authentik provider.
    - **Appname**: the Client ID from the authentik provider.
    - **Caption**: the label shown on the new login button on the Icinga Web 2 sign-in page, for example `Sign in with authentik`.
    - **Groups to sync** _(optional)_: a comma-separated list of the groups that should be imported into the Icinga database (see the info box below).
    - **Required Groups** _(optional)_: a comma-separated list of groups the user must be a member of in order to be allowed to log in via authentik. Leave empty to allow any authenticated authentik user.
    - **Enabled**: toggle on. The provider is disabled by default and the login button is only displayed once this switch is enabled.
    - **Enforce Https on redirect urls**: toggle on if Icinga Web 2 runs behind an HTTPS-terminating reverse proxy.
4. Click **Create Provider** to save the configuration.

:::info
The **Groups to sync** field defaults to `*`, which causes the module to import **every** group the authenticated user is a member of into the Icinga Web 2 database. In most authentik environments this means importing many groups that are not relevant to Icinga. To keep the database tidy and avoid permission noise in **Access Control**, restrict this field to a comma-separated list of the specific groups that are actually used for Icinga, for example `icinga-admins, icinga-users`.
:::

### Grant permissions to authentik users and groups

After a user logs in via authentik for the first time, the user (and any synced groups) is created in the Icinga Web 2 database without any permissions. To grant access, assign **Roles** to the user or group under **Configuration** > **Authentication** > **Roles**.

:::info
Configuring Icinga Web 2 roles and permissions in detail is out of scope for this guide. Refer to the [Icinga Web 2 access control documentation](https://icinga.com/docs/icinga-web/latest/doc/06-Security/) for the specifics.
:::

## Configuration verification

To confirm that authentik is properly configured with Icinga Web 2, log out of Icinga Web 2 and click the new authentik login button on the sign-in screen. You should be redirected to authentik to log in, then redirected back to the Icinga Web 2 dashboard.

## Resources

- [RISE-GmbH OIDC module for Icinga Web 2 on GitHub](https://github.com/RISE-GmbH/icingaweb2-module-oidc)
- [RISE-GmbH OIDC module configuration documentation](https://github.com/RISE-GmbH/icingaweb2-module-oidc/blob/main/doc/03-Configuration.md)
