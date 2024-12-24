---
title: Integrate with Chronograf
sidebar_label: Chronograf
---

# Chronograf

<span class="badge badge--secondary">Support level: Community</span>

## What is Chronograf

> Chronograf allows you to quickly see the data that you have stored in InfluxDB so you can build robust queries and alerts. It is simple to use and includes templates and libraries to allow you to rapidly build dashboards with real-time visualizations of your data.
>
> -- https://www.influxdata.com/time-series-platform/chronograf/

## Preparation

The following placeholders will be used:

-   `chronograf.company` is the FQDN of the Chronograf install
-   `authentik.company` is the FQDN of the authentik install.

## authentik configuration

From the administration interface of your authentik installation, navigate to **Applications -> Applications** on the left sidebar, and create an OAuth2/OpenID provider using the wizard. Take note of the application slug, client ID, and Client secret as you will need them later. Set a strict redirect URI to `https://service.company/oauth/authentik/callback`, and set the signing key to any availi, then submit the wizard.

## Service Configuration

Add the following environm variables to your Chronograf setup. This setup is also valid if you configured Chronograf with a config file. You may wish to limit/alter the `GENERIC_SCOPES` and `GENERERIC_API_KEY` options to match your preferences.

:::Note
You can visit the [Chronograf configuration option documentation](https://docs.influxdata.com/chronograf/v1/administration/config-options/) for more information.
:::

```txt
PUBLIC_URL=https://chronograf.company
TOKEN_SECRET=<A random secret>
JWKS_URL=https://authentik.company/application/o/<Application slug from before>/jwks/
GENERIC_NAME=authentik
GENERIC_CLIENT_ID=<Client ID from above>
GENERIC_CLIENT_SECRET=<Client secret from above>
GENERIC_SCOPES=email,profile,openid
GENERIC_DOMAINS=authentik.company
GENERIC_AUTH_URL=https://authentik.company/application/o/authorize/
GENERIC_TOKEN_URL=https://auth.authentik.company/application/o/token/
GENERIC_API_URL=https://auth.authentik.company/application/o/userinfo/
GENERIC_API_KEY=email
```

After restarting your Chronograf instance, a "Login with authentik" button should be visible on the login page.

