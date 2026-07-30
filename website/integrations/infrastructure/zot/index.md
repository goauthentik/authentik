---
title: Integrate with zot
sidebar_label: zot
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is zot?

> zot is an OCI-native container registry for distributing container images and OCI artifacts.
>
> -- https://zotregistry.dev

## Preparation

The following placeholders are used in this guide:

- `zot.company` is the FQDN of the zot installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of zot with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it is required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - **Protocol Settings**:
            - **Redirect URI**:
                - `Strict` `Authorization`: `https://zot.company/zot/auth/callback/oidc`.
            - **Signing Key**: select any available signing key.
        - Note the **Client ID** and **Client Secret** values because they are required later.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## zot configuration

To support the integration of zot with authentik, configure zot to use authentik as its OpenID Connect provider.

1. Create the OIDC credentials file with the **Client ID** and **Client Secret** values from the authentik provider created earlier:

```json title="/etc/zot/oidc-credentials.json"
{
    "clientid": "<Client ID from authentik>",
    "clientsecret": "<Client Secret from authentik>"
}
```

2. Edit the zot configuration file to enable OpenID Connect authentication. Set `externalUrl` to the public URL that users use to access zot.

```json title="/etc/zot/config.json"
{
    "http": {
        "externalUrl": "https://zot.company",
        "port": "8080",
        "auth": {
            "openid": {
                "providers": {
                    "oidc": {
                        "credentialsFile": "/etc/zot/oidc-credentials.json",
                        "issuer": "https://authentik.company/application/o/<application_slug>/",
                        "keypath": "",
                        "scopes": ["openid", "profile", "email"]
                    }
                }
            }
        }
    }
}
```

:::info Command-line clients
OpenID Connect social login is for the zot web interface. To push or pull images with command-line clients, log in to zot through authentik and generate an API key in zot.
:::

3. Restart zot to apply the configuration changes:

```bash
systemctl restart zot
```

## Configuration verification

To confirm that authentik is properly configured with zot, log out of zot and open the zot integration from authentik. On the zot login page, click **SIGN IN WITH OIDC**. After you authenticate with authentik, zot signs you in.

## Resources

- [zot Documentation - User Authentication and Authorization](https://zotregistry.dev/v2.1.18/articles/authn-authz/#social-login-using-openidoauth2)
