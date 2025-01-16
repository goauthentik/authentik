---
title: Integrate with Cloudflare Access
sidebar_label: Cloudflare Access
---

# Cloudflare Access

<span class="badge badge--secondary">Support level: Community</span>

## What is Cloudflare Access

> Cloudflare Access is a secure, cloud-based zero-trust solution for managing and authenticating user access to internal applications and resources.
>
> -- https://www.cloudflare.com/zero-trust/products/access/

## Preparation

The following placeholders are used in this guide:

- `company.cloudflareaccess.com` is the FQDN of your Cloudflare Access subdomain.
- `authentik.company` is the FQDN of the authentik installation.

To proceed, you need to register for a free Cloudflare Access account and have both a Cloudflare account and a publicly accessible authentik instance with a trusted SSL certificate.

## authentik configuration

1. From the Admin interface, navigate to **Applications** -> **Applications**.
2. Use the wizard to create a new application and provider. During this process:
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://company.cloudflareaccess.com/cdn-cgi/access/callback`.
    - Select any available signing key.

## Cloudflare Access configuration

1. Open the [Cloudflare Access dashboard](https://one.dash.cloudflare.com) and navigate to **Settings** -> **Authentication**.
2. Click **Login methods**, and then select **Add** -> **OpenID Connect**.
3. From the authentik provider you created earlier, copy the following details and paste them into the corresponding fields:
    - **Client ID** -> App ID
    - **Client Secret** -> Client Secret
    - **Authorize URL** -> Auth URL
    - **Token URL** -> Token URL
    - **JWKS URL** -> Certificate URL
4. Click **Save**.
5. Click **Test** to verify the login provider.
