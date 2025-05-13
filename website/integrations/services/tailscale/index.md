---
title: Integrate with Tailscale
sidebar_label: Tailscale
support_level: community
---

## What is Tailscale

> Tailscale is a mesh VPN service that creates secure, encrypted, peer-to-peer connections between devices across different networks using the WireGuard protocol.
>
> -- https://tailscale.com

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Tailscale with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://login.tailscale.com/a/oauth_response`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Tailscale configuration

:::info
Tailscale requires a properly configured WebFinger endpoint at `.well-known/webfinger` on the domain used for your email. Set this up according to your web server or application specifications.

Use this JSON template for your WebFinger response:
```json
{
    "links": [
        {
            "href": "https://authentik.company",
            "rel": "http://openid.net/specs/connect/1.0/issuer"
        }
    ],
    "subject": "acct:your@email.com"
}
```

**Important:** Replace `your@email.com` with the administrator email you'll use when creating your Tailnet. This email must match exactly in both the WebFinger configuration and during Tailscale setup.
:::

1. Visit the [Tailscale sign up page](https://login.tailscale.com/start) and click **Sign up with OIDC**.
2. Enter the administrator email, select `authentik` as the identity provider type, and click **Get OIDC Issuer**.
3. Fill the form:
    - Enter the Client ID copied from authentik in the **Client ID** field.
    - Enter the Client secret copied from authentik in the **Client secret** field.
    - Keep the default value `consent` in the **Prompts** section.
4. Click **Sign up with OIDC** and follow the prompts to complete the Tailscale-specific configuration.

## Resources

- [Tailscale SSO documentation](https://tailscale.com/kb/1240/sso-custom-oidc)

## Configuration verification

To verify the integration with Tailscale, log out and attempt to log back in. When you enter an email address from your configured SSO domain, you should be redirected to authentik.