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

The following placeholders are used in this guide:

- `hoarder.company` is the FQDN of the Hoarder installation.
- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

### Provider settings

In authentik, under **Applications** -> **Providers** of the **Admin interface**, create a new **OAuth2/OpenID Provider** with the desired settings.

- Name: `hoarder`
- Redirect URI: `https://hoarder.company/api/auth/callback/custom`

Everything else is up to you, just make sure to grab the client ID and the client secret!

### Application settings

In authentik, under **Applications** -> **Applications** of the **Admin interface**, create a new Application with the **Create** button that uses `hoarder` provider.
Optionally apply access restrictions to the application.

## Hoarder configuration

In Hoarder, you'll need to add these environment variables:

```sh
NEXTAUTH_URL=https://hoarder.company
OAUTH_CLIENT_ID=<Client ID from authentik>
OAUTH_CLIENT_SECRET=<Client secret from authentik>
OAUTH_WELLKNOWN_URL=https://authentik.company/application/o/hoarder/.well-known/openid-configuration
OAUTH_PROVIDER_NAME=authentik
OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING=true
# Optional: You can add this if you only want to allow login with Authentik
# DISABLE_PASSWORD_AUTH=true
# Optional but highly recommended:
# DISABLE_SIGNUPS=true
```

Finally, restart the Hoarder server and test your configuration.
