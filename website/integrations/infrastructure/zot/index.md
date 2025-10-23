---
title: Integrate with Zot
sidebar_label: Zot
support_level: community
---

## What is Zot

> Zot is an OCI-native container registry for distributing container images and OCI artifacts. Zot was accepted to CNCF on December 13, 2022 at the Sandbox maturity level.
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
- **Configure the Provider**: provide a name (`zot-registry` in this example or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - **Protocol Settings**:
        - **Redirect URI**:
            - Strict: `https://zot.company/zot/auth/callback/oidc`.
        - **Signing Key**: select any available signing key.

- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Zot configuration

To support the integration of authentik with Zot, you need to configure OIDC authentication.

1. configure `/etc/zot/oidc-credentials.json` 
```json
{
    "clientid": "clientid",
    "clientsecret": "clientsecret"
}
```

2. configure `/etc/zot/config.json`
```json
{
    "http": {
        "externalUrl": "https://zot.company",
        "port": "8080",
        "auth": {
            "openid": {
                 "providers": {
                     "oidc": {
                         "credentialsFile": "/etc/zot/oidc-credentials.json",
                         "issuer": "https://authentik.company/application/o/zot-registry/",
                         "keypath": "",
                         "scopes": ["openid", "profile", "email", "groups"]
                     }
                 }
             }
        }
    }
}
```


## Configuration verification

To confirm that authentik is properly configured with Zot, log out of Zot, locate the "SIGN IN WITH OIDC" button on the login page, click on it, and ensure you can successfully log in using Single Sign-On.
