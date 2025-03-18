---
title: Integrate with Tandoor
sidebar_label: Tandoor
support_level: community
---

## What is Tandoor

> Application for managing recipes, planning meals, building shopping lists and more.
>
> -- https://github.com/TandoorRecipes/recipes

## Preparation

The following placeholders are used in this guide:

- `tandoor.company` is the FQDN of the tandoor installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

Create an **OAuth2/OpenID Application and Provider** under **Applications** -> **Applications** via the **Create with Provider** button, using the following settings:

- Name: `tandoor`
- Redirect URIs/Origins (RegEx): `https://tandoor.company/accounts/oidc/authentik/login/callback/`

Everything else is up to you, just make sure to grab the client ID and the client secret!

## Tandoor configuration

Add the following lines to your tandoor environment `.env` file. Make sure to edit with the client ID, client secret and server URL from your Authentik instance.

```sh
# Authentik OAuth2/OpenID configuration
SOCIAL_PROVIDERS=allauth.socialaccount.providers.openid_connect
SOCIALACCOUNT_PROVIDERS='{"openid_connect":{"APPS":[{"provider_id":"authentik","name":"authentik","client_id":"<Client ID from authentik>","secret":"<Client Secret from authentik>","settings":{"server_url":"https://authentik.company/application/o/<application slug>/.well-known/openid-configuration"}}]}}
'
```

Restart the Tandoor docker service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Tandoor, log out of Tandoor, locate the "Sign in with authentik" button on the login page, click on it, and ensure you can successfully log in using Single Sign-On.
