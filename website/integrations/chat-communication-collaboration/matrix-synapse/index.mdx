---
title: Integrate with Matrix Synapse
sidebar_label: Matrix Synapse
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Matrix Synapse?

> Synapse is an open source Matrix homeserver implementation, written and maintained by Element. Matrix is the open standard for secure and interoperable real-time communications.
>
> -- https://github.com/element-hq/synapse

## Preparation

The following placeholders are used in this guide:

- `matrix.company` is the public FQDN where Matrix clients reach Synapse.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Matrix Synapse with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** as it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://matrix.company/_synapse/client/oidc/callback`.
        - Select any available RSA-based **Signing Key**. Matrix Synapse does not support ECC keys for authentik.
        - Leave **Encryption Key** empty.
        - Under **Advanced protocol settings**, set **Logout URI** to `https://matrix.company/_synapse/client/oidc/backchannel_logout` and **Logout Method** to `Back-channel`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Matrix Synapse configuration

Synapse's Docker images and Debian packages include the OIDC dependencies. If you installed Synapse in a virtual environment, install the OIDC extras before enabling this configuration:

```shell
/path/to/env/bin/pip install matrix-synapse[oidc]
```

Add the following configuration to your Synapse configuration file:

```yaml title="homeserver.yaml"
oidc_providers:
    - idp_id: authentik
      idp_name: authentik
      discover: true
      backchannel_logout_enabled: true
      issuer: "https://authentik.company/application/o/<application_slug>/"
      client_id: "<Client ID from authentik>"
      client_secret: "<Client Secret from authentik>"
      scopes:
          - "openid"
          - "profile"
          - "email"
      user_mapping_provider:
          config:
              localpart_template: "{{ user.preferred_username }}"
              display_name_template: "{{ user.preferred_username|capitalize }}"

jwt_config:
    enabled: true
    secret: "<Client Secret from authentik>"
    algorithm: "RS256"
```

The `display_name_template` line can use `{{ user.name|capitalize }}` if your authentik users have names and you want Synapse display names to use those values.

Restart Synapse to apply the configuration.

## Configuration verification

To confirm that authentik is properly configured with Matrix Synapse, open your Matrix client, choose your Synapse homeserver, and sign in with authentik. You should be redirected to authentik for authentication and then redirected back to your Matrix client.

## Resources

- [Synapse OpenID Connect configuration](https://element-hq.github.io/synapse/latest/openid.html)
- [Synapse `oidc_providers` configuration reference](https://element-hq.github.io/synapse/latest/usage/configuration/config_documentation.html#oidc_providers)
- [Synapse `jwt_config` configuration reference](https://element-hq.github.io/synapse/latest/usage/configuration/config_documentation.html#jwt_config)
