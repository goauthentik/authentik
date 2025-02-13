---
title: Integrate with EspoCRM
sidebar_label: EspoCRM
---

# Integrate with EspoCRM

<span class="badge badge--secondary">Support level: Community</span>

## What is EspoCRM?

> EspoCRM is a CRM (customer relationship management) web application that allows users to store, visualize, and analyze their company's business-related relationships such as opportunities, people, businesses, and projects.
>
> -- https://www.espocrm.com/

:::warning
This guide does _not_ cover Team Mapping. Please refer to EspoCRM's [documentation](https://docs.espocrm.com/administration/oidc/#team-mapping).
:::

## Preparation

The following placeholders are used in this guide:

- `crm.<your_company>` is the FQDN of the EspoCRM installation.
- `authentik.<your_company>` is the FQDN of the authentik installation.
- `_SLUG_` is the slug you choose upon application create in authentik.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

1. Log into authentik as an admin, and navigate to **Applications** --> **Applications**.
2. Click **Create with Wizard**.

:::info
Alternatively, use our legacy process and click **Create**. The legacy process requires that the application and its configuration provider be configured separately.
:::

3. In the _New Application_ wizard, define the application details, and then define the provider details with the following parameters:

- **Provider Type**: `OAuth2/OIDC (Open Authorization/OpenID Connect)`

- **Authorization Flow**: `default-provider-authorization-explicit-consent (Authorize Application)`
- **Client Type**: `Confidential`
- **Redirect URIs/Origins**: `https://crm.<your_company>/oauth-callback.php`
- **Scopes**: OpenID, Email, Profile, Proxy outpost
- **Subject Mode**: `Based on the User's username` (**OR** your preferred method; you can use the same username in authentik and EspoCRM)
- **Signing Key**: Select any available key

Note the `Client ID` and `Client Secret` values.

## EspoCRM configuration

### Access the OIDC auth

1. Login to your admin user at `crm.<your_company>`.

2. In EspoCRM at Administration > Authentication, select the OIDC method. Below, on the same form, a OIDC panel will appear.

### Configure the OIDC auth

1. Configure the following variables:

- **Client ID**: enter the `Client ID` from authentik
- **Client Secret**: enter the `Client Secret` from authentik
- **Authorization Redirect URI**: `https://crm.<your_company>/oauth-callback.php`
- **Fallback Login**: _Select this option if you want EspoCRM's login as fallback._
- **Allow OIDC login for admin users**: _Select this option if you want EspoCRM's admin users to be able to log in via OIDC._

    _The following values are listed as slugs for clarity. An example for the first variable is included._

    You can also view the full URLs on the provider's page in authentik's Admin interface.

- **Authorization Endpoint**: `/application/o/authorize/`
    - (e.g. `https://crm.<your_company>/application/o/authorize/`)
- **Token Endpoint**: `/application/o/token/`
- **JSON Web Key Set Endpoint**: `/application/o/_SLUG_/jwks/`
- **Logout URL**: `application/o/_SLUG_/end-session/`

### Confirm the configuration

1. Select the `Save` option.

2. Access your EspoCRM instance (e.g. `crm.<your_company>`) in a private browser, and select `Sign In.`

- You will be presented with your authentik log-in screen.

- Enter your authentik credentials to proceed to EspoCRM!
