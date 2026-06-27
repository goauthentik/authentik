---
title: Integrate with Cisco Secure Firewall Management Center
sidebar_label: Cisco Secure FMC
support_level: community
---

## What is Cisco Secure Firewall Management Center?

> The Cisco Secure Firewall Management Center (FMC) is your administrative nerve center for managing critical Cisco network security solutions. It provides complete and unified management over firewalls, application control, intrusion prevention, URL filtering, and advanced malware protection.
>
> -- https://www.cisco.com/c/en/us/products/collateral/security/firesight-management-center/datasheet-c78-736775.html
> see also https://www.cisco.com/c/en/us/products/security/firepower-management-center/index.html

## Preparation

The following placeholders are used in this guide:

- `fmc.company` is the FQDN of the Cisco FMC.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::info
This is based on authentik 2026.5.3 and Cisco FMC 7.6.5
Only settings that have been modified from default have been listed.
:::

## authentik configuration

To support the integration of Cisco Secure Firewall Management Center with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

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
            - The FMC requires that SSO usernames be formatted as email addresses. Therefore, set the **NameID Property Mapping** to `authentik default SAML Mapping: Email`
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the Cisco FMC provider.
3. Click **Download** under **Download signing certificate**. You will import this certificate into Cisco FMC.

## Cisco FMC configuration

1. Log in to the Cisco Secure Firewall Management Center web interface as an administrator.
2. Click the **gear icon** in the upper-right corner and choose **Users**.
3. Click the **Single Sign-On (SSO)** tab.
4. Click the toggle button to enable SSO.
5. Under **Select the SAML provider**, select `Other`, then click **Next**.
6. Configure the **Identity Provider (IdP) Settings**:
    - **Identity Provider Single Sign-On (SSO) URL**: `https://authentik.company/application/saml/<application_slug>/init/`
    - **Identity Provider Issuer**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **X.509 Certificate**: Open the signing certificate you downloaded from authentik using Notepad. Copy-and-paste the text of the certificate into this field.
    - Under **Advanced Configuration (Role Mapping)**, set **Default User Role** to `Administrator`.
7. Click **Next**.
8. Click **Save** to apply the configuration.

<!--
6. Confirm the **Service Provider (SP) Settings** that FMC auto-populates:
    - **SP Entity ID**: should match the **Audience** value (`https://fmc.company`) configured in the authentik provider.
    - **ACS URL**: should match the **ACS URL** value (`https://fmc.company/saml/SSO`) configured in the authentik provider.

:::info User accounts
FMC requires that a local user account exists with a username matching the value sent in the SAML assertion before an SSO login can succeed. Ensure that local accounts are pre-created in FMC, or confirm that your FMC version supports just-in-time (JIT) user provisioning via SSO.
:::
-->

## Configuration verification

To confirm that authentik is properly configured with Cisco Secure Firewall Management Center, navigate to your FMC login page and select the SSO login option. Complete the authentik sign-in flow. After authentication, FMC should redirect you back and grant access to the management interface.

## Resources

- [Cisco - Configure Firepower Management Center Access through SSO Authentication with Okta](https://www.cisco.com/c/en/us/support/docs/security/firepower-management-center/216331-configure-firepower-management-center-ac.html)
