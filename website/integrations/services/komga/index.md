---
title: Komga
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Komga

From https://komga.org/

:::note
Komga is a free and open source comics/mangas media server
:::

## Preparation

The following placeholders will be used:

-   `komga.company` is the FQDN of the Komga install.
-   `authentik.company` is the FQDN of the authentik install.

Create an application in authentik. Create an OAuth2/OpenID provider with the following parameters:

-   Client Type: Confidential
-   Scopes: OpenID, Email and Profile
-   Signing Key: Select any available key
-   Redirect URIs: https://komga.company/login/oauth2/code/authentik

Note the Client ID and Client Secret values. Create an application, using the provider you've created above. Note the slug of the application you've created.

## Komga

Add the following block to your Komga application.yml. If this does not exist, you must create it.

:::info
For more info, see https://komga.org/installation/oauth2.html#advanced-configuration
:::

```yaml
komga:
    ## Comment if you don't want automatic account creation.
    oauth2-account-creation: true
spring:
    security:
        oauth2:
            client:
                registration:
                    authentik:
                        client-id: "client-id"
                        client-secret: "client-secret"
                        client-name: client-name
                        scope: openid,profile,email
                        authorization-grant-type: authorization_code
                        redirect-uri: "https://komga.company/login/oauth2/code/authentik"
                provider:
                    authentik:
                        issuer-uri: https://authentik.company/application/o/app-slug/
                        user-name-attribute: preferred_username
```
