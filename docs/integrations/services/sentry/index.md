# Sentry Integration

## What is Sentry

From https://sentry.io

!!! note ""
    Sentry provides self-hosted and cloud-based error monitoring that helps all software
    teams discover, triage, and prioritize errors in real-time.

    One million developers at over fifty thousand companies already ship
    better software faster with Sentry. Won’t you join them?

## Preparation

The following placeholders will be used:

-   `sentry.company` is the FQDN of the Sentry install.
-   `passbook.company` is the FQDN of the passbook install.

Create an application in passbook. Create an OpenID provider with the following parameters:

-   Client Type: `Confidential`
-   Response types: `code (Authorization Code Flow)`
-   JWT Algorithm: `RS256`
-   Redirect URIs: `https://sentry.company/auth/sso/`
-   Scopes: `openid email`

## Sentry

**This guide assumes you've installed Sentry using [getsentry/onpremise](https://github.com/getsentry/onpremise)**

- Add `sentry-auth-oidc` to `onpremise/sentry/requirements.txt` (Create the file if it doesn't exist yet)
- Add the following block to your `onpremise/sentry/sentry.conf.py`:
```
OIDC_ISSUER = "passbook"
OIDC_CLIENT_ID = "<Client ID from passbook>"
OIDC_CLIENT_SECRET = "<Client Secret from passbook>"
OIDC_SCOPE = "openid email"
OIDC_DOMAIN = "https://passbook.company/application/oidc/"
```
