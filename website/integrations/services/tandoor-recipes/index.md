---
title: Tandoor Recipes
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Tandoor Recipes

> Tandoor Recipes is an easy-to-use, powerful self-hosted food recipe manager.
>
> -- https://docs.tandoor.dev/

Tandoor Recipes uses Django Allauth as the authentication engine. It supports OpenID Connect.

## Preparation

The following placeholders will be used:

-   `tandoor.company` is the FQDN of the Tandoor Recipes install.
-   `authentik.company` is the FQDN of the authentik install.

### Provider

Create a Provider in authentik with the following parameters:

-   Client type

    Confidential


-   Client ID

    Take note of the Client ID.

-   Client Secret

    Take note of the Client Secret.

-   Redirect URIs/Origins (RegEx)

    https://tandoor.company/accounts/authentik/login/callback/

-   Signing Key

    authentik Self-signed Certificate

-   Leave the rest as the default options.

### Application

Create an Application with the following parameters:

-   Name: tandoor

-   Provider: tandoor

-   Leave the rest as the default options.

## Tandoor Recipe

-   Set the following environment variables on your Tandoor Recipes installation (please make sure to use the correct values for `server_url`, `client_id` and `secret`):

-   Restart Tandoor, you should now see `Sign In Via Authentik` button.

-   If you want to set your authentik user as the administrator, log in as an administrator. Then navigate to  `https://tandoor.company/admin/auth/user/`, click the user you want to make an administrator, and select the `Superuser status` and `Staff status`.
