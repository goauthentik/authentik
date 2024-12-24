---
title: Integrate with Komga
sidebar_label: Komga
---

# Komga

<span class="badge badge--secondary">Support level: Community</span>

## What is Komga

> Komga is an open-source comic and manga server that lets users organize, read, and stream their digital comic collections with ease.
>
> -- [https://service.xyz](https://komga.org/)

## Preparation

The following placeholders will be used:

- `komga.company` is the FQDN of the Komga install.
- `komga.company` is the FQDN of the authentik install.

## authentik configuration

From the main page of the **authentik admin interface**, navigate to **Applications** -> **Applications** and follow the wizard to create a new service. Take note of the Client ID, Client Secret, and slug as you will need them later. Then, set the redirect URI to `https://komga.company/login/oauth2/code/authentik` and select any availible signing key.

## Komga configuration

Update Komga's `application.yml` to include the following options:

:::info
All configuration options can be found in [Komga's OAuth2 Advanced configuration documentation](https://komga.org/docs/installation/oauth2/#advanced-configuration).
:::

```yml
spring:
  security:
    oauth2:
      client:
        registration:
          authentik:
            provider: authentik
            client-id: <client-id>
            client-secret: <client secret>
            client-name: authentik
            scope: openid,email
            authorization-grant-type: authorization_code
            redirect-uri: "{baseUrl}/{action}/oauth2/code/{registrationId}"
        provider:
          authentik:
            user-name-attribute: sub
            issuer-uri: https://authentik.company/application/o/<application slug>/
```
