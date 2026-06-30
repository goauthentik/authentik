---
title: Integrate with Headscale
sidebar_label: Headscale
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Headscale?

> Headscale is an open source, self-hosted implementation of the Tailscale control server.
>
> -- https://headscale.net

## Preparation

The following placeholders are used in this guide:

- `headscale.company` is the FQDN of the Headscale installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Headscale with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://headscale.company/oidc/callback`.
        - Select any available signing key.
        - Leave **Encryption Key** empty.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Headscale configuration

To support the integration of Headscale with authentik, update the `oidc` section in the Headscale configuration file:

```yaml showLineNumbers title="/etc/headscale/config.yaml"
oidc:
    issuer: "https://authentik.company/application/o/<application_slug>/"
    client_id: "<Client ID from authentik>"
    client_secret: "<Client Secret from authentik>"
    # OIDC scopes to request (defaults: "openid", "profile", "email")
    # Additional scopes can be added to request extra user information
    scope: ["openid", "profile", "email", "custom"]
    # Passed on to the browser login request - used to tweak behaviour for the OIDC provider (optional)
    extra_params:
        domain_hint: acmecorp.net

    # Reject authentication if user doesn't match these criteria (optional)
    allowed_domains:
        - acmecorp.net

    # Group-based access control (optional)
    allowed_groups:
        - /headscale

    # Specific user allowlist (optional)
    allowed_users:
        - dominic@acmecorp.net

    pkce:
        enabled: true
```

If you store the client secret outside the configuration file, use Headscale's `client_secret_path` setting or the `HEADSCALE_OIDC_CLIENT_SECRET` environment variable instead of `client_secret`.

Restart Headscale for the configuration changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Headscale, open Headscale and sign in with OIDC.

## Resources

- [Headscale OIDC documentation](https://headscale.net/stable/ref/oidc/#basic-configuration)
- [Headscale configuration documentation](https://headscale.net/stable/ref/configuration/)
