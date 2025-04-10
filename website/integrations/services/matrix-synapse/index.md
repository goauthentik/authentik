---
title: Integrate with Matrix Synapse
sidebar_label: Matrix Synapse
---

# Integrate with Matrix Synapse

<span class="badge badge--secondary">Support level: Community</span>

## What is Matrix Synapse

> Matrix is an open source project that publishes the Matrix open standard for secure, decentralised, real-time communication, and its Apache licensed reference implementations.
>
> -- https://matrix.org/

## Preparation

The following placeholders are used in this guide:

- `matrix.company` is the FQDN of the Matrix installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Create an application in authentik. Create an OAuth2/OpenID provider with the following parameters:

- Client Type: `Confidential`
- Scopes: OpenID, Email and Profile
- Signing Key: Select any available key
- Redirect URIs: `https://matrix.company/_synapse/client/oidc/callback`

Note the Client ID and Client Secret values. Create an application, using the provider you've created above. Note the slug of the application you've created.

## Matrix

Add the following block to your Matrix config

:::info
For more info, see https://matrix-org.github.io/synapse/latest/openid.html?highlight=authentik#authentik
:::

```yaml
oidc_providers:
    - idp_id: authentik
      idp_name: authentik
      discover: true
      issuer: "https://authentik.company/application/o/app-slug/"
      client_id: "*client id*"
      client_secret: "*client secret*"
      scopes:
          - "openid"
          - "profile"
          - "email"
      user_mapping_provider:
          config:
              localpart_template: "{{ user.preferred_username }}"
              display_name_template: "{{ user.name|capitalize }}"
```
