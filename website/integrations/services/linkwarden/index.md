---
title: Linkwarden
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Linkwarden

> Linkwarden is an open-source collaborative bookmark manager to collect, organize and preserve webpages.
>
> -- https://linkwarden.app/

## Preparation

The following placeholders will be used:

-   `linkwarden.company` is the FQDN of the Service install.
-   `authentik.company` is the FQDN of the authentik install.

## Service configuration

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

1. Navigate to the **Admin Interface**, and create a new **OAuth2 / OpenID Provider** under the **Providers** category.
2. Take note of the **Client ID** and **Client Secret**.
3. Add the following redirect URL under **Redirect URIs/Origins (RegEx)**: `https://linkwarden.company/api/v1/auth/callback/authentik`.
4. Click **Finish**, then create a new application.

Linkwarden should now be configured to use authentik as a SSO provider.
