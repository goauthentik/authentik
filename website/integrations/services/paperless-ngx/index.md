---
title: Paperless-ngx
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Paperless-ngx

> Paperless-ngx is an application that indexes your scanned documents and allows you to easily search for documents and store metadata alongside your documents. It was a fork from paperless-ngx, in turn a fork from the original Paperless, neither of which are maintained any longer.
>
> -- https://github.com/paperless-ngx/paperless-ngx

## Preparation

The following placeholders will be used:

-   `paperless.company` is the FQDN of the Paperless-ngx install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

### Step 1 - OAuth2/OpenID Provider

Create a OAuth2/OpenID Provider (under Applications/Providers) with these settings:

    Name : Paperless
    Redirect URI: https://paperless.company/accounts/oidc/authentik/login/callback/

### Step 2 - Application

Create an application (under Resources/Applications) with these settings:

    Name: Paperless
    Slug: paperless
    Provider: Paperless

## Paperless Configuration

Add the following environment variables to your Paperless-ngx setup. If you are using Docker Compose, then add the following to your docker-compose.yml file:

```yaml
PAPERLESS_APPS: allauth.socialaccount.providers.openid_connect
PAPERLESS_SOCIALACCOUNT_PROVIDERS: >
    {
      "openid_connect": {
        "APPS": [
          {
            "provider_id": "authentik",
            "name": "Authentik",
            "client_id": "< Client ID >",
            "secret": "< Client Secret >",
            "settings": {
              "server_url": "https://authentik.company/application/o/paperless/.well-known/openid-configuration"
            }
          }
        ],
        "OAUTH_PKCE_ENABLED": "True"
      }
    }
```

Now restart your container:
`docker compose down && docker compose up -d`

## Finished

Now you can access Paperless-ngx by logging in with authentik.

To add authentik authentication to an existing user, log in to Paperless with local authentication, click the profile icon in the top-right, click My Profile, then Connect new social account.
