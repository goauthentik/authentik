---
title: Integrate with espoCRM
sidebar_label: espoCRM
---

# espoCRM

<span class="badge badge--secondary">Support level: Community</span>

## What is espoCRM?

> EspoCRM is a web application that allows users to see, enter and evaluate all your company relationships regardless of the type. People, companies, projects or opportunities — all in an easy and intuitive interface.
>
> -- https://www.espocrm.com/

:::warning
This guide does _not_ cover Team Mapping. Please refer to espoCRM's [documentation](https://docs.espocrm.com/administration/oidc/#team-mapping).
:::

## Preparation

The following placeholders will be used:

-   `crm.company` is the FQDN of the espoCRM install. 
-   `authentik.company` is the FQDN of the authentik install.
- `_SLUG_` is the slug you choose upon application create in authentik.

Create an application in authentik and note the slug you choose, as this will be used later (`_SLUG_`).
In the Admin Interface, go to **Applications** -> **Providers**. Create a **OAuth2/OpenID** provider with the following parameters:

- **Authorization Flow**: `default-provider-authorization-explicit-consent (Authorize Application)`
- **Client Type**: `Confidential`
- **Redirect URIs/Origins**: `https://_crm.company_/oauth-callback.php`
- **Scopes**: OpenID, Email, Profile, Proxy outpost
- **Subject Mode**: `Based on the User's username` (**OR** your preferred method; I personally use the same username in authentik and espoCRM)
- **Signing Key**: Select any available key

Note the `Client ID` and `Client Secret` values. 
Create an application, using the provider you've created above.

## espoCRM configuration
### Access the OIDC auth
1. Login to your admin user at `crm.company`.

2. In EspoCRM at Administration > Authentication, select the OIDC method. Below, on the same form, a OIDC panel will appear.

### Configure the OIDC auth
1. Configure the following variables:
- **Client ID**: enter the `Client ID` from authentik
- **Client Secret**: enter the `Client Secret` from authentik 
- **Authorization Redirect URI**: `https://_crm.company_/oauth-callback.php`
- **Fallback Login**: _Select this option if you want espoCRM's login as fallback._
- **Allow OIDC login for admin users**: _Select this option if you want espoCRM's admin users to be able to log in via OIDC._

    _The following values I listed as slugs for clarity. I included an example for the first variable.
The full URLs can also be found on the provider's page in authentik's UI._

- **Authorization Endpoint**: `/application/o/authorize`
    - (e.g. `https://_crm.company_/application/o/authorize`)
- **Token Endpoint**: `/application/o/token/`
- **JSON Web Key Set Endpoint**: `/application/o/_SLUG_/jwks`
- **Logout URL**: `application/o/_SLUG_/end-session/`

### Confirm the configuration 
1. Select the `Save` option.

2. Access `crm.company` in a private browser, and select `Sign In.`
- You will be presented with your authentik log-in screen.

- Enter your credentials to proceed to espoCRM!
