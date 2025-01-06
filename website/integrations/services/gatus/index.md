---
title: Integrate with Gatus
sidebar_label: Gatus
---

# Gatus

<span class="badge badge--secondary">Support level: Community</span>

## What is Gatus?

> Gatus is a free and open source project for endpoint monitoring. It allows many types of monitoring from pings or http requests to DNS checking and certification expiration. This is all done through yaml files.
>
> -- https://github.com/TwiN/gatus

## Preparation

The following placeholders are used in this guide:

- `gatus.company` is the FQDN of the Gatus install.
- `authentik.company` is the FQDN of the authentik install.

## authentik configuration

Create an OIDC provider with the following settings:

- Name: 'gatus'
- Redirect URL: 'https://gatus.company/authorization-code/callback'

Everything else is up to you and what you want, just don't forget to grab the client ID and secret!

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
