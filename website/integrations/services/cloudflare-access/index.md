---
title: Cloudflare Access
---
<span class="badge badge--secondary">Support level: Community</span>

## What is Cloudflare Access

> Cloudflare Access is a secure, cloud-based zero-trust solution for managing and authenticating user access to internal applications and resources.
>
> -- https://www.cloudflare.com/zero-trust/products/access/

## Preparation

Before you begin, note the following placeholders:

- `company.cloudflareaccess.com`: Your Cloudflare Access subdomain FQDN
- `authentik.company`: Your authentik install FQDN

Prerequisites:
- A free Cloudflare Access account
- A Cloudflare account
- A publicly accessible authentik instance with a trusted SSL certificate

## authentik configuration

To set up authentik for Cloudflare Access:

1. Log in to your authentik instance and access the Admin interface.

2. Create a new OAuth2/OpenID Provider:
   - Navigate to **Application** > **Providers**
   - Choose **OAuth2/OpenID Provider**
   - Set the authorization flow to **Authorize Application**
   - Set the client type to **Confidential**
   - Set the redirect URI to `https://company.cloudflareaccess.com/cdn-cgi/access/callback`
   - Ensure the signing key is set to **Authentik Self-signed Certificate**

3. Create a new application:
   - Give it a name
   - Set the provider to the one you just created
   - Ensure the **Policy engine mode** is set to **ANY, any policy must match to grant access**

## Cloudflare Access configuration

To configure Cloudflare Access:

1. Navigate to the [Cloudflare One dashboard](https://one.dash.cloudflare.com).

2. Add a login method:
   - Go to **Settings** > **Authentication**
   - Click **Add** under **Login methods** and select **OpenID Connect**
   - Enter a name for your login method

3. Configure the OpenID Connect settings:
   - Copy the following details from your authentik provider settings:
     - **Client ID** → App ID
     - **Client Secret** → Client Secret
     - **Authorize URL** → Auth URL
     - **Token URL** → Token URL
     - **JWKS URL** → Certificate URL

4. Save your settings and test the login provider to verify the configuration.
