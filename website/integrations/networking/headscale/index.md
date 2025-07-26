---
title: Integrate with Headscale
sidebar_label: Headscale
support_level: community
---

## What is Headscale

> [Headscale](https://github.com/juanfont/headscale) is an open source alternative to the Tailscale coordination server and can be self-hosted for a single tailnet. Headscale is a re-implemented version of the Tailscale coordination server, developed independently and completely separate from Tailscale, with its own independent community of users and developers.
>
> -- https://headscale.net

## Preparation

The following placeholders are used in this guide:

- `headscale.company` is the FQDN of the Headscale installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Headscale with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://headscale.company/oidc/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Headscale configuration

To support the integration of Headscale with authentik, you'll need to update the `config.yaml` file of your Headscale deployment:

```yaml showLineNumbers title="/etc/headscale/config.yaml"
oidc:
    # Do not start Headscale until it can fetch authentik's OIDC configuration
    only_start_if_oidc_is_available: true
    issuer: "https://authentik.company/application/o/<headscale-slug>/"
    client_id: "<Client ID from authentik>"
    # There are three ways to configure the client secret (choose one):
    #
    # 1. Directly in the config file (not recommended for production):
    client_secret: "<Client secret from authentik>"
    #
    # 2. From a file path (supports environment variables, works with systemd's LoadCredential):
    # client_secret_path: "${CREDENTIALS_DIRECTORY}/oidc_client_secret"
    #
    # 3. From an environment variable:
    # The HEADSCALE_OIDC_CLIENT_SECRET environment variable will be used automatically if set

    # OIDC scopes to request (defaults: "openid", "profile", "email")
    # Additional scopes can be added to request extra user information
    scope: ["openid", "profile", "email", "custom"]
    # Passed on to the browser login request – used to tweak behaviour for the OIDC provider (optional)
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
        method: S256

    # Email Domain Handling:
    # When strip_email_domain is true: "user@acmecorp.net" becomes username "user"
    # When strip_email_domain is false: "user@acmecorp.net" becomes username "user.acmecorp.net"
    strip_email_domain: true
```

## Configuration verification

To verify the integration with Headscale, log out and attempt to log back in using OIDC. When attempting to log in, you'll be redirected to your Headscale installation, which then forwards you to authentik before returning to Headscale, though the exact flow may vary slightly depending on the client platform.

## Resources

- [Headscale OIDC documentation](https://headscale.net/stable/ref/oidc/#basic-configuration)
