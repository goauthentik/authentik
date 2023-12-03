---
title: Chronograf oauth
---

<span class="badge badge--secondary">Support level: Community</span>

## Chronograf

Part of the TICK stack from Influxdata (https://www.influxdata.com/). 

Influxdata say: "Chronograf allows you to quickly see the data that you have stored in InfluxDB so you can build robust queries and alerts. It is simple to use and includes templates and libraries to allow you to rapidly build dashboards with real-time visualizations of your data."
[Read more](https://www.influxdata.com/time-series-platform/chronograf/).

## Preparation

The following placeholders will be used:

-   `service.company` is the FQDN of the Chronograf install. E.g. chronograf.domain.tld
-   `authentik.company` is the FQDN of the authentik install.

## Service Configuration

:::Note
In this configuration, "GENERIC_NAME" is what will appear on the Chronograf login page.
:::

The following environement variables can be configured using the official Chronograf docker container (https://hub.docker.com/_/chronograf?tab=description). They are also valid for a standalone configuration using an environment file. You may wish to limit/alter the 'GENERIC_SCOPES' and GENERERIC_API_KEY to match your install preferences.

Additional resources for service configuraton:
https://docs.influxdata.com/chronograf/v1/administration/config-options/
```
      PUBLIC_URL: "https://service.company"
      TOKEN_SECRET: "<generate_a_token_secret>"
      JWKS_URL: "https://auth.authentik.company/application/o/chrono/jwks/"
      GENERIC_NAME: "Authentik"
      GENERIC_CLIENT_ID: "<client id from Authentik>"
      GENERIC_CLIENT_SECRET: "<client secret from Authentik>"
      GENERIC_SCOPES: "email,profile,openid"
      GENERIC_DOMAINS: "authentik.company"
      GENERIC_AUTH_URL: "https://auth.authentik.company/application/o/authorize/"
      GENERIC_TOKEN_URL: "https://auth.authentik.company/application/o/token/"
      GENERIC_API_URL: "https://auth.authentik.company/application/o/userinfo/"
      GENERIC_API_KEY: "email"
```
In this configuration, "GENERIC_NAME" is what will appear on the Chronograf login page:

![image](https://github.com/tomlawesome/authentik/assets/76453276/c14a4694-563b-4a94-9cd4-162c4e543bd7)


## Authentik configuration

Create an oAuth provider for your service, along with an application. Authentik makes the required endpoints available by default, so no advanced/special configuration is required for generic oauth.  

:::Note
Only settings that have been modified from default have been listed.
:::

Protocol Settings

    Name: Chronograf

    Signing Key: Select any available key

    Redirect URIs/Origins: Authentik will save the first succesful redirect URI if you enter * in this field, but the following should work..https://servuce.company/oauth/Authentik/callback


