---
title: Integrate with Gatus
sidebar_label: Gatus
support_level: community
---

## What is Gatus?

> Gatus is a free and open source project for endpoint monitoring. It allows many types of monitoring from pings or http requests to DNS checking and certification expiration. This is all done through yaml files.
>
> -- https://github.com/TwiN/gatus

## Preparation

The following placeholders are used in this guide:

- `gatus.company` is the FQDN of the Gatus installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Gatus with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>gatus.company</em>/authorization-code/callback</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Gatus configuration

In the `config.yaml` file of Gatus, add the following:

```yml
security:
    oidc:
        issuer-url: https://authentik.company/application/o/gatus/
        client-id: "CLIENT_ID"
        client-secret: "CLIENT_SECRET"
        redirect-url: https://gatus.company/authorization-code/callback
        scopes: [openid]
```

:::note
Gatus auto-updates the configuration about every 30 seconds. However, if it does not pick up the changes, just restart the instance.
:::
