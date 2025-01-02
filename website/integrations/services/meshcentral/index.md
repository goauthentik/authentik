---
title: Integrate with MeshCentral
sidebar_label: MeshCentral
---

<span class="badge badge--secondary">Support level: Community</span>

## What is MeshCentral

> MeshCentral is a free, open source, web-based platform for remote device management.
>
> -- https://meshcentral.com

## Preparation

The following placeholders are used in this guide:

- `meshcentral.company` is the FQDN of the MeshCentral install.
- `authentik.company` is the FQDN of the authentik install.

## authentik configuration

Create an OAuth2/OpenID provider with the following parameters:

- Client Type: `Confidential`
- Redirect URIs: `https://meshcentral.company/auth-oidc-callback`
- Scopes: OpenID, Email and Profile
- Signing Key: Select any available key

Note the Client ID and Client Secret values.

Next, create an application, using the provider you've created above.

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
