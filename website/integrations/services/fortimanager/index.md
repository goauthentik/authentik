---
title: Integrate with FortiManager
sidebar_label: FortiManager
support_level: community
---

## What is FortiManager

> FortiManager supports network operations use cases for centralized management, best practices compliance, and workflow automation to provide better protection against breaches.
>
> FortiManager is a paid enterprise product.
>
> -- https://www.fortinet.com/products/management/fortimanager

## Preparation

The following placeholders are used in this guide:

- `fgm.company` is the FQDN of the FortiManager installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of FortiManager with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to <kbd>https://<em>fortimanager.company</em>/saml/?acs</kbd>.
    - Set the **Issuer** to <kbd>https://<em>authentik.company</em>/application/saml/<em>application-slug</em>/sso/binding/redirect/</kbd>.
    - Set the **Service Provider Binding** to `Post`.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## FortiManager Configuration

Navigate to `https://fgm.company/p/app/#!/sys/sso_settings` and select SAML SSO settings to configure SAML.

Select 'Service Provider (SP)' under Single Sign-On Mode to enable SAML authentication.

Set the Field 'SP Address' to the FortiManager FQDN 'fgm.company'. (This gives you the URLs to configure in authentik)

Set the Default Login Page to either 'Normal' or 'Single-Sign On'. (Normal allows both local and SAML authentication vs only SAML SSO)

FortiManager create a new user by default if one does not exist so you will need to set the Default Admin Profile to the permissions you want any new users to have. (We created a no_permissions profile to assign by default)

Set the Field 'IdP Type' to 'Custom'

Set the Field `IdP entity ID` to `https://authentik.company/application/saml/fgm/sso/binding/redirect/`.

Set the Field `IdP Login URL` to `https://authentik.company/application/saml/fgm/sso/binding/redirect/`.

Set the Field `IdP Logout URL` to `https://authentik.company/`

For the Field 'IdP Certificate" Import your authentik cert. (Self Signed or real)
