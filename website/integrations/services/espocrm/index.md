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

- `espocrm.company` is the FQDN of the EspoCRM installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of EspoCRM with authentik, you need to create an application/provider pair in authentik.

**Create an application and provider in authentik**

In the authentik Admin Interface, navigate to **Applications** > **Applications** and click **[Create with Provider](/docs/add-secure-apps/applications/manage_apps#add-new-applications)** to create an application and provider pair. (Alternatively, you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>espocrm.company</em>/oauth-callback.php</kbd>.
    - Select any available signing key.
    - Under **Advanced Protocol Settings**, set **Subject mode** to be `Based on the Users's username`.
- **Configure Bindings** _(optional):_ you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user’s **My applications** page.

## EspoCRM configuration

To configure EspoCRM for OpenID Connect authentication, navigate to your instance and login as an administrator user. Then, navigate to **Administration** > **Authentication** and select the **OIDC method**. A panel allowing you to configure OIDC settings should appear.

Configure the following fields:

- **Client ID**: The Client ID from authentik
- **Client Secret**: The Client Secret from authentik
- **Authorization Redirect URI**: <kbd>https://<em>espocrm.company</em>/oauth-callback.php</kbd>
- **Fallback Login**: Toggle this option if you wish to have the option to use EspoCRM's integrated login as a fallback.
- **Allow OIDC login for admin users**: Toggle this option if you wish to allow administrator users to log in with OIDC.
- **Authorization Endpoint**: <kbd>https://<em>authentik.company</em>/application/o/authorize</kbd>
- **Token Endpoint**: <kbd>https://<em>authentik.company</em>/application/o/token</kbd>
- **JSON Web Key Set Endpoint**: <kbd>https://<em>authentik.company</em>/application/o/<em>your-application-slug</em>/jwks</kbd>
- **Logout URL**: <kbd>https://<em>authentik.company</em>/application/o/<em>your-application-slug</em>/end_session</kbd>

## Ressources

- [EspoCRM administrator documentation on OpenID Connect authentication](https://docs.espocrm.com/administration/oidc/)

## Configuration verification

To confirm that authentik is properly configured with EspoCRM, log out and log back in via authentik. Clicking the "Login" button on the homepage should redirect you to authentik.
