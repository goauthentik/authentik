---
title: Tandoor Recipes
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Tandoor Recipes

> Tandoor Recipes is an easy-to-use, powerful self-hosted food recipe manager.
>
> -- https://docs.tandoor.dev/

Tandoor Recipy uses Django Allauth as the authentication engine. It supports OpenID Connect.

## Preparation

The following placeholders will be used:

-   `tandoor.company` is the FQDN of the Tandoor Recipes install.
-   `authentik.company` is the FQDN of the authentik install.

### Provider

Create an Provider in authentik with the following parameters:

-   Client type

    Confidential


-   Client ID

    Take note off Client ID.

-   Client Secret

    Take note off Client Secret.

-   Redirect URIs/Origins (RegEx)

    https://tandoor.company/accounts/authentik/login/callback/

-   Signing Key

    authentik Self-signed Certificate

-   Leave the rest on default

### Application

Create a Application with the following parameters:

-   Name: tandoor

-   Provider: tandoor

-   Leave rest on default

## Tandoor Recipy

-   Set the following environment variables on your Tandoor Recipes installation (please make sure to use the correct values for `server_url`, `client_id` and `secret`):

-   Restart Tandoor, you should now see `Sign In Via Authentik` button.

-   If you want to set your authentik user as administrator, log in as an administrator, then you can do so in the https://tandoor.company/admin/auth/user/ click the user you want to make admin, and mark the `Superuser status` and `Staff status`.
