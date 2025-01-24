---
title: Integrate with Chronograf
sidebar_label: Chronograf
---

# Chronograf

<span class="badge badge--secondary">Support level: Community</span>

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

1. From the authentik Admin interface navigate to **Applications** -> **Applications** on the left sidebar.
2. Create an application and an OAuth2/OpenID provider using the [wizard](https://docs.goauthentik.io/docs/add-secure-apps/applications/manage_apps#add-new-applications).
    - Note the application slug, client ID, and client secret, as they will be required later.
    - Set a strict redirect URI to `https://chronograf.company/oauth/authentik/callback`.
    - Choose a signing key (any available key is acceptable).
3. Complete and submit the settings to close the wizard.

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
