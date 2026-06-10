---
title: Integrate with Cloudflare Access
sidebar_label: Cloudflare Access
support_level: community
---

## What is Cloudflare Access?

> Cloudflare Access is a secure, cloud-based zero-trust solution for managing and authenticating user access to internal applications and resources.
>
> -- https://www.cloudflare.com/zero-trust/products/access/

## Preparation

The following placeholders are used in this guide:

- `company.cloudflareaccess.com` is the FQDN of your Cloudflare Access team domain.
- `authentik.company` is the FQDN of the authentik installation.

To proceed, you need a Cloudflare account with Cloudflare Zero Trust enabled and a publicly accessible authentik instance with a trusted SSL certificate.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::info Cloudflare Dashboard SSO
Looking to integrate authentik with your Cloudflare Dashboard? See our [integration guide](../../platforms/cloudflare/index.md) for more information.
:::

## authentik configuration

To support the integration of Cloudflare Access with authentik, you need to create an application/provider pair in authentik.

Cloudflare uses your Cloudflare Access team name in the callback URL. You can find the team name in the Cloudflare dashboard under **Settings** > **Team name and domain** > **Team name**.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://company.cloudflareaccess.com/cdn-cgi/access/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Cloudflare Access configuration

1. Open the [Cloudflare dashboard](https://one.dash.cloudflare.com) and go to **Zero Trust** > **Integrations** > **Identity providers**.
2. Under **Your identity providers**, click **Add new identity provider**, and then select **OpenID Connect**.
3. Configure the identity provider using values from the authentik provider created earlier:
    - **Name**: enter a descriptive name, for example `authentik`.
    - **App ID**: enter the **Client ID** from authentik.
    - **Client Secret**: enter the **Client Secret** from authentik.
    - **Auth URL**: enter `https://authentik.company/application/o/authorize/`.
    - **Token URL**: enter `https://authentik.company/application/o/token/`.
    - **Certificate URL**: enter `https://authentik.company/application/o/<application_slug>/jwks/`.
4. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with Cloudflare Access, open Cloudflare Access, go to **Authentication** > **Login methods**, and click **Test** next to the authentik login method. Complete the login flow and verify that Cloudflare displays a successful test result.

## Resources

- [Cloudflare Access Generic OIDC documentation](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/generic-oidc/)
