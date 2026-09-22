---
title: Integrate with MeshCentral
sidebar_label: MeshCentral
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is MeshCentral?

> MeshCentral is a free, open source, web-based platform for remote device management.
>
> -- https://meshcentral.com

## Preparation

The following placeholders are used in this guide:

- `meshcentral.company` is the FQDN of the MeshCentral installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of MeshCentral with authentik, you need to create an application and provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://meshcentral.company/auth-oidc-callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## MeshCentral configuration

Edit the `config.json` file for your MeshCentral deployment, and add the OIDC authentication strategy to the domain that should use authentik. The example below configures the default MeshCentral domain, `""`.

For Docker deployments, `config.json` is located in the host directory that is mapped to `/opt/meshcentral/meshcentral-data`.

```json title="config.json"
{
    "domains": {
        "": {
            "authStrategies": {
                "oidc": {
                    "issuer": "https://authentik.company/application/o/<application_slug>/",
                    "client": {
                        "client_id": "<Client ID from authentik>",
                        "client_secret": "<Client Secret from authentik>"
                    }
                }
            }
        }
    }
}
```

Restart your MeshCentral instance to apply the updated configuration.

## Configuration verification

To confirm that authentik is properly configured with MeshCentral, open your MeshCentral instance and click the OpenID Connect sign-in button. After you authenticate with authentik, MeshCentral should redirect you back and sign you in.

## Resources

- [MeshCentral documentation: Using the OpenID Connect Strategy](https://docs.meshcentral.com/meshcentral/openidConnectStrategy/)
