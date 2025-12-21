---
title: Integrate with Zot
sidebar_label: Zot
support_level: community
---

## What is Zot

> Zot is an OCI-native container registry for distributing container images and OCI artifacts.
>
> -- https://zotregistry.dev

## Preparation

The following placeholders are used in this guide:

- `zot.company` is the FQDN of the Zot installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Zot with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - **Protocol Settings**:
        - **Redirect URI**:
            - Strict: `https://zot.company/zot/auth/callback/oidc`.
        - **Signing Key**: select any available signing key.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://zot.company/zot/auth/callback/oidc`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Zot configuration

To support the integration of Zot with authentik, you must configure it to use authentik as it's authentication provider.

1. Create the OIDC credentials file with the **Client ID** and **Client Secret** values from the authentik provider created earlier:

```json title="/etc/zot/oidc-credentials.json"
{
    "clientid": "<client_id_from_authentik>",
    "clientsecret": "<client_secret_from_authentik>"
}
```

2. Edit the Zot configuration file to enable OpenID Connect authentication:

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

3. Restart Zot to apply the configuration changes:

```bash
systemctl restart zot
```

## Configuration verification

To confirm that authentik is properly configured with Zot, first log out of Zot. Then click the **SIGN IN WITH OIDC** button on the login page and you should be redirected to authentik. Once authenticated, you should be signed into Zot.

## Resources

- [Zot Documentation - Social login using OpenID/OAuth2](https://zotregistry.dev/v2.1.10/articles/authn-authz/#social-login-using-openidoauth2)
