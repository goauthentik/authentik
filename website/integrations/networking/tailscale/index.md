---
title: Integrate with Tailscale
sidebar_label: Tailscale
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Tailscale?

> Tailscale is a mesh VPN service that creates secure, encrypted, peer-to-peer connections between devices across different networks using the WireGuard protocol.
>
> -- https://tailscale.com

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

This guide covers creating a new tailnet with custom OIDC. To migrate an existing tailnet to custom OIDC, contact Tailscale support after configuring WebFinger.

:::info WebFinger endpoint required
Tailscale requires a WebFinger endpoint at `https://example.com/.well-known/webfinger` on the domain used for your administrator email address. Set this up according to your web server or application specifications.

Use this JSON template for your WebFinger response:

```json
{
    "subject": "acct:admin@example.com",
    "links": [
        {
            "href": "https://authentik.company/application/o/<application_slug>/",
            "rel": "http://openid.net/specs/connect/1.0/issuer"
        }
    ]
}
```

Replace `admin@example.com` with the administrator email address that you will use when creating your tailnet. The domain in the email address must match the domain where the WebFinger endpoint is served and the domain you will use for Tailscale. The issuer URL must exactly match the issuer in authentik's OpenID configuration, and both the WebFinger endpoint and authentik issuer must be reachable by Tailscale.
:::

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Tailscale with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required for the WebFinger response.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://login.tailscale.com/a/oauth_response`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Tailscale configuration

1. Open Tailscale's [Sign up with OIDC](https://login.tailscale.com/start/oidc) page.
2. Enter the administrator email address that matches your WebFinger endpoint and click **Get OIDC Issuer**. If prompted for an identity provider type, select **authentik**.
3. Set the following configurations:
    - **Client ID**: enter the client ID from authentik.
    - **Client secret**: enter the client secret from authentik.
4. Click **Sign up with OIDC** and authenticate with authentik using the administrator email address from the previous step.

## Configuration verification

To verify the integration with Tailscale, open Tailscale and log in using an email address from your configured SSO domain. You should be redirected to authentik and then back to the Tailscale admin console.

## Resources

- [Tailscale custom OIDC providers documentation](https://tailscale.com/docs/integrations/identity/custom-oidc)
