---
title: Integrate with FortiManager
sidebar_label: FortiManager
---

# Integrate with FortiManager

<span class="badge badge--secondary">Support level: Community</span>

## What is FortiManager

> FortiManager is an enterprise solution that enables centralized network management, ensures compliance with best practices, and automates workflows to enhance breach protection.
>
> -- https://www.fortinet.com/products/management/fortimanager

## Preparation

The following placeholders are used in this guide:

- `fortimanager.company` is the FQDN of the FortiManager installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation only lists the settings that have been changed from their default values. Please verify your changes carefully to avoid any issues accessing your application.
:::

## authentik configuration

To support the integration of FortiManager with authentik, you need to create an application/provider pair in authentik.

**Create an application and provider in authentik**

In the authentik Admin Interface, navigate to **Applications** > **Applications** and click **[Create with Provider](/docs/add-secure-apps/applications/manage_apps#add-new-applications)** to create an application and provider pair. (Alternatively, you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to <kbd>https://<em>fortimanager.company</em>/saml/?acs</kbd>.
    - Set the **Issuer** to <kbd>https://<em>authentik.company</em>/application/saml/<em>application-slug</em>/sso/binding/redirect/</kbd>.
    - Set the **Service Provider Binding** to `Post`.
- **Configure Bindings** _(optional):_ you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user’s **My applications** page.

## FortiManager Configuration

1. Navigate to <kbd>https://<em>fortimanager.company</em>/p/app/#!/sys/sso_settings</kbd> and select **SAML SSO Settings** to configure SAML.
2. Under **Single Sign-On Mode**, choose **Service Provider (SP)** to enable SAML authentication.
3. Set the **SP Address** field to the FortiManager FQDN, <kbd>fortimanager.company</kbd>. This provides the URLs needed for configuration in authentik.
4. Choose the **Default Login Page** as either **Normal** or **Single Sign-On**. Selecting **Normal** allows both local and SAML authentication, while **Single Sign-On** restricts login to SAML only.
5. By default, FortiManager creates a new user if one does not exist. Set the **Default Admin Profile** to assign the desired permissions to new users. A `no_permissions` profile is created by default for this purpose.
6. Set the **IdP Type** field to **Custom**.
7. For the **IdP Entity ID** field, enter: <kbd>https://<em>authentik.company</em>/application/saml/<em>application-slug</em>/sso/binding/redirect/</kbd>
8. Set the **IdP Login URL** to: <kbd>https://<em>authentik.company</em>/application/saml/<em>application-slug</em>/sso/binding/redirect/</kbd>
9. Set the **IdP Logout URL** to: <kbd>https://<em>authentik.company</em>/</kbd>
10. In the **IdP Certificate** field, import your authentik certificate (either self-signed or valid).

## Ressources

- [Community post on the Fortinet forum](https://community.fortinet.com/t5/FortiAnalyzer/Technical-Tip-Configure-SAML-SSO-login-with-Azure-AD/ta-p/198324)

## Configuration verification

To confirm that authentik is properly configured with FortiManager, log out and log back in via authentik.
