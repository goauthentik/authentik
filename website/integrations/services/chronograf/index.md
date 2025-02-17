---
title: Integrate with Chronograf
sidebar_label: Chronograf
support_level: community
---

## What is Chronograf

> Chronograf lets you quickly visualize the data stored in InfluxDB, enabling you to build robust queries and alerts. It is simple to use and comes with templates and libraries for rapidly creating dashboards with real-time data visualizations.
>
> -- https://www.influxdata.com/time-series-platform/chronograf/

## Preparation

The following placeholders are used in this guide:

- `chronograf.company` is the FQDN of your Chronograf installation.
- `authentik.company` is the FQDN of your authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Chronograf with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create.)**
3. Log in to authentik as an admin, and open the authentik Admin interface.
4. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create.)**

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>chronograf.company</em>/oauth/authentik/callback/</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Chronograf configuration

Add the following environment variables to your Chronograf setup. If you are using a configuration file for Chronograf, these settings can also be included there. You may modify the values for `GENERIC_SCOPES` and `GENERIC_API_KEY` to suit your specific requirements.

:::info
Refer to the [Chronograf configuration options documentation](https://docs.influxdata.com/chronograf/v1/administration/config-options/) for more information.
:::

```
PUBLIC_URL=https://chronograf.company
TOKEN_SECRET=<A random secret>
JWKS_URL=https://authentik.company/application/o/<application-slug>/jwks/
GENERIC_NAME=authentik
GENERIC_CLIENT_ID=<client-id>
GENERIC_CLIENT_SECRET=<client-secret>
GENERIC_SCOPES=email,profile,openid
GENERIC_DOMAINS=authentik.company
GENERIC_AUTH_URL=https://authentik.company/application/o/authorize/
GENERIC_TOKEN_URL=https://auth.authentik.company/application/o/token/
GENERIC_API_URL=https://auth.authentik.company/application/o/userinfo/
GENERIC_API_KEY=email
USE_ID_TOKEN=true
```

After restarting your Chronograf instance, the login page should display a "Log in with authentik" button.
