---
title: Integrate with Linkwarden
sidebar_label: Linkwarden
---

# Integrate with Linkwarden

<span class="badge badge--secondary">Support level: Community</span>

## What is Linkwarden

> Linkwarden is an open-source collaborative bookmark manager used to collect, organize, and preserve webpages.
>
> -- https://linkwarden.app/

## Preparation

The following placeholders are used in this guide:

- `linkwarden.company` is the FQDN of the Linkwarden installation.
- `authentik.company` is the FQDN of the authentik installation.

## Linkwarden configuration

To configure Linkwarden to use authentik, add the following values to your `.env` file:

```
NEXT_PUBLIC_AUTHENTIK_ENABLED=true
AUTHENTIK_CUSTOM_NAME=authentik # Optionally set a custom provider name. Will be displayed on the login page
AUTHENTIK_ISSUER=https://authentik.company/application/o/linkwarden
AUTHENTIK_CLIENT_ID=<Your Client ID>
AUTHENTIK_CLIENT_SECRET=<Your Client Secret>
```

After making these changes, restart your Docker containers to apply the new configuration.

## authentik configuration

1. Access the **Admin Interface** in on your authentik installation.
2. Create a new **OAuth2 / OpenID Provider**.
3. Note the generated **Client ID** and **Client Secret**.
4. In the provider settings, add this redirect URL under **Redirect URIs/Origins (RegEx)**: `https://linkwarden.company/api/v1/auth/callback/authentik`
5. Click **Finish** to save the provider configuration.
6. Create a new application associated with this provider.

Once completed, Linkwarden should be successfully configured to use authentik as its Single Sign-On SSO provider.
