---
title: Gravitee
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Gravitee

> Gravitee.io API Management is a flexible, lightweight and blazing-fast Open Source solution that helps your organization control who, when and how users access your APIs.
>
> It offers an easy to use GUI to setup proxies for APIs, rate limiting, api keys, caching, OAUTH rules, a portal that can be opened to the public for people to subscribe to APIs, and much more.
>
> -- https://github.com/gravitee-io/gravitee-api-management

## Preparation

The following placeholders will be used:

-   `gravitee.company` is the FQDN of the Gravitee install.
-   `authentik.company` is the FQDN of the authentik install.
-   `applicationName` is the Application name you set.

### Step 1 - authentik

In authentik, under _Providers_, create an _OAuth2/OpenID Provider_ with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**

-   Name: applicationName
-   Client ID: Copy and Save this for Later
-   Client Secret: Copy and Save this for later
-   Redirect URIs/Origins:

```
https://gravitee.company/user/login
https://gravitee.company/console/ # Make sure to add the trailing / at the end, at the time of writing it does not work without it
```

Now, under _Applications_, create an application with the name `applicationName` and select the provider you've created above.

### Step 2 - Gravitee

In the Gravitee Management Console, head to _Organizations_(gravitee.company/console/#!/organization/settings/identities) , under _Console_, _Authentication_, click _Add an identity provider_, select _OpenID Connect_, and fill in the following:

:::note
Only settings that have been modified from default have been listed.
:::

-   Allow portal authentication to use this identity provider: enable this
-   Client ID: Client ID from step 1
-   Client Secret: Client Secret from step 1
-   Token Endpoint: `https://authentik.company/application/o/token/`
-   Authorize Endpoint: `https://authentik.company/application/o/authorize/`
-   Userinfo Endpoint: `https://authentik.company/application/o/userinfo/`
-   Userinfo Logout Endpoint: `https://authentik.company/if/session-end/applicationName/`
-   Scopes: `email openid profile`
