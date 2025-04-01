---
title: Integrate with Matrix Synapse
sidebar_label: Matrix Synapse
support_level: community
---

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

## authentik configuration

To support the integration of Matrix Synapse with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>matrix.company</em>/\_synapse/client/oidc/callback</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Matrix configuration

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
