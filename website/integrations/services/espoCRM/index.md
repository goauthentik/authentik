---
title: Integrate with EspoCRM
sidebar_label: EspoCRM
support_level: community
---

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

To support the integration of EspoCRM with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>espocrm.company</em>/oauth-callback.php</kbd>.
    - Select any available signing key.
    - Under **Advanced Protocol Settings**, set **Subject mode** to be `Based on the Users's username`.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

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
