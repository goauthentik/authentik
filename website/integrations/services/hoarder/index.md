---
title: Integrate with Hoarder
sidebar_label: Hoarder
---

# Hoarder

<span class="badge badge--secondary">Support level: Community</span>

## What is Hoarder

> A self-hostable bookmark-everything app (links, notes and images) with AI-based automatic tagging and full-text search.
>
> -- https://hoarder.app/

## Preparation

The following placeholders will be used:

-   `hoarder.company` is the FQDN of the hoarder install.
-   `authentik.company` is the FQDN of the authentik install.

## Authentik configuration

**Provider Settings**

In authentik under **Providers**, create an OAuth2/OpenID Provider with these settings:

-   Name: `hoarder`
-   Redirect URI: `https://hoarder.company/api/auth/callback/custom`

Everything else is up to you, just make sure to grab the client ID and the client secret!

**Application Settings**

Create an application that uses `hoarder` provider. Optionally apply access restrictions to the application.

## Hoarder configuration

In hoarder you'll need to add these environment variables:

```sh
NEXTAUTH_URL=https://hoarder.company
OAUTH_CLIENT_ID=client_id_from_provider
OAUTH_CLIENT_SECRET=client_secret_from_provider
OAUTH_WELLKNOWN_URL=https://authentik.company/application/o/hoarder/.well-known/openid-configuration
OAUTH_PROVIDER_NAME=Authentik
OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING=true
# Optional: You can add this if you only want to allow login with Authentik
# DISABLE_PASSWORD_AUTH=true
# Optional but highly recommended:
# DISABLE_SIGNUPS=true
```

Finally, restart the hoarder server and test your configuration.
