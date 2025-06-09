---
title: Integrate with MeshCentral
sidebar_label: MeshCentral
support_level: community
---

## What is MeshCentral

> MeshCentral is a free, open source, web-based platform for remote device management.
>
> -- https://meshcentral.com

## Preparation

The following placeholders are used in this guide:

- `meshcentral.company` is the FQDN of the MeshCentral installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of MeshCentral with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://meshcentral.company/auth-oidc-callback`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## MeshCentral configuration

Edit the `config.json` file for your MeshCentral deployment, and add the following code in the `domains:` subsection:

:::info
For Docker deployments, the `config.json` should be located in the directory on the host machine you mapped to `/opt/meshcentral/meshcentral-data`.
:::

:::info
If you need to enable advanced OIDC configurations, please refer to the [Using the OpenID Connect Strategy](https://ylianst.github.io/MeshCentral/meshcentral/openidConnectStrategy/) section in the MeshCentral documentation for detailed instructions.
:::

```json
    "domains": {
            "authStrategies": {
                "oidc": {
                    "issuer": "https://authentik.company/application/o/meshcentral/",
                    "clientid": "<Client ID>",
                    "clientsecret": "<Client Secret>",
                    "newAccounts": true
                }
            },
```

To ensure everything is setup correctly, restart your MeshCentral instance and visit the main page. You should be greeted with a new button to allow signing in with OIDC.
