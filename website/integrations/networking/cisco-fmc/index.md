---
title: Integrate with Cisco Secure Firewall Management Center
sidebar_label: Cisco Secure FMC
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Cisco Secure Firewall Management Center?

> Cisco Secure Firewall Management Center (FMC) centralizes management for Cisco Secure Firewall policies, events, intrusion prevention, URL filtering, and malware protection.
>
> -- https://www.cisco.com/site/us/en/products/security/firewalls/secure-firewall-management-center/index.html

## Preparation

The following placeholders are used in this guide:

- `fmc.company` is the FQDN of the Cisco FMC.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

This guide was tested with Cisco Secure Firewall Management Center 7.6.5.

## authentik configuration

To support the integration of Cisco Secure Firewall Management Center with authentik, you need to create an application/provider pair in authentik.

Cisco FMC requires the SAML NameID and SSO account usernames to be valid email addresses. Ensure that each authentik user who signs in to Cisco FMC has an email address.

### Create a role mapping property mapping _(optional)_

If you want Cisco FMC to assign user roles from SAML attributes, create a SAML property mapping that sends this application's entitlements to Cisco FMC.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Create a property mapping with the following values:
    - **Name**: `Cisco FMC roles`
    - **SAML Attribute Name**: `fmc_roles`
    - **Expression**:

        ```python
        return [
            entitlement.name
            for entitlement in request.user.app_entitlements(provider.application)
        ]
        ```

5. Click **Finish** to save the property mapping.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because you will use it when configuring Cisco FMC.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://fmc.company/saml/acs`.
        - Set the **Audience** to `https://fmc.company/saml/metadata`.
        - Under **Advanced protocol settings**:
            - Set the **Signing Certificate** to the certificate authentik should use to sign SAML responses.
            - Enable **Sign responses**.
            - Set the **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
            - If you created the optional role mapping property mapping, add `Cisco FMC roles` to **Selected User Property Mappings**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Create application entitlements _(optional)_

Use [application entitlements](/docs/add-secure-apps/applications/manage_apps/#application-entitlements) to represent the Cisco FMC role assignment values that this application should send.

1. Open the Cisco FMC application that you created in the authentik Admin interface.
2. Click the **Application entitlements** tab.
3. Create one entitlement for each Cisco FMC role assignment value that users should be able to receive, such as `FMC-Administrator`.
4. Open each entitlement and bind the users or groups that should receive it.

### Download the signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the Cisco FMC provider.
3. Click **Download** under **Download signing certificate**. You will import this certificate into Cisco FMC.

## Cisco Secure Firewall Management Center configuration

1. Log in to the Cisco Secure Firewall Management Center web interface as an administrator.
2. Click the **gear icon** in the upper-right corner and choose **Users**.
3. Click the **Single Sign-On (SSO)** tab.
4. Click the toggle button to enable SSO.
5. Under **Select the SAML provider**, select `Other`, then click **Next**.
6. Configure the **Identity Provider (IdP) Settings**:
    - **Identity Provider Single Sign-On (SSO) URL**: enter the **SAML Endpoint** from the authentik SAML provider, such as `https://authentik.company/application/saml/<application_slug>/`.
    - **Identity Provider Issuer**: enter the **EntityID/Issuer** from the authentik SAML provider, such as `https://authentik.company/application/saml/<application_slug>/metadata/`.
    - **X.509 Certificate**: paste the contents of the signing certificate that you downloaded from authentik.
7. Under **Advanced Configuration (Role Mapping)**, review the **Default User Role**. Cisco FMC assigns this role to SSO users that do not match a role mapping.
8. If you configured the optional `Cisco FMC roles` property mapping in authentik, set **Group Member Attribute** to `fmc_roles`, and then enter a regular expression for each Cisco FMC user role that should match an entitlement value, such as `^FMC-Administrator$`.
9. Click **Next**.
10. Click **Save** to apply the configuration.

## Configuration verification

To confirm that authentik is properly configured with Cisco Secure Firewall Management Center, navigate to your FMC login page and select the SSO login option. Complete the authentik sign-in flow. After authentication, FMC should redirect you back and grant access to the management interface.

## Resources

- [Cisco Secure Firewall Management Center Administration Guide - SAML single sign-on](https://www.cisco.com/c/en/us/td/docs/security/secure-firewall/management-center/admin/760/management-center-admin-76/system-users.html#Configure_SAML_Single_SignOn_)
