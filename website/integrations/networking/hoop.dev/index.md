---
title: Integrate with Hoop.dev
sidebar_label: Hoop.dev
support_level: community
---

## What is Hoop.dev

> Hoop.dev is an access gateway for databases and servers with AI-powered automations that eliminate cumbersome access policies and break-glass workflows without compromising security.
>
> -- https://hoop.dev

## Preparation

The following placeholders are used in this guide:

- `hoop.company` is the FQDN of the Hoop.dev installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Hoop.dev with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://hoop.company/api/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Hoop.dev configuration

To support the integration of Hoop.dev with authentik, you must configure it to use authentik as it's identity provider. 

1. Create the Kubernetes ConfigMap for `hoopgateway` deploment or set corresponding environment variables with the **Client ID**, **Client Secret** and **slug** values from the Authentik provider created earlier:

```yaml
config:
    AUTH_METHOD: "oidc"
    IDP_CLIENT_ID: "<client_id_from_authentik>"
    IDP_CLIENT_SECRET: "<client_secret_from_authentik>"
    IDP_GROUPS_CLAIM: "groups"
    IDP_ISSUER: "https://authentik.company/application/o/<application_slug>/"
```

2. Restart `hoopgateway` service to apply the configuration changes.

## Configuration verification

To confirm that Authentik is properly configured with Hoop.dev, first create client config file. Then run login command and you should be redirected to Authentik. Once authenticated, you should be signed into Hoop.dev network.

```bash
hoop config create --api-url https://hoop.company
hoop login
```

## Resources

- [Hoop.dev Documentation - Oauth2/OIDC Authentication](https://hoop.dev/docs/setup/configuration/env-vars#oauth2%2Foidc-authentication)
