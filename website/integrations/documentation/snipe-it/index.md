---
title: Integrate with Snipe-IT
sidebar_label: Snipe-IT
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Snipe-IT?

> A free open source IT asset/license management system.
>
> -- https://snipeitapp.com

## Preparation

The following placeholders are used in this guide:

- `inventory.company` is the FQDN of the Snipe-IT installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning HTTPS required
Configure Snipe-IT with an HTTPS `APP_URL` before you enable SAML. Snipe-IT generates its SAML entity ID, ACS URL, SLS URL, and metadata URL from that value.
:::

:::info Local login fallback
If SAML login is enabled and you need to use Snipe-IT's local login form, open `https://inventory.company/login?nosaml`.
:::

## authentik configuration

To support the integration of Snipe-IT with authentik, you need an LDAP application/provider pair, an LDAP bind service account, an LDAP outpost, and a SAML application/provider pair. LDAP sync creates the Snipe-IT users, and SAML authenticates those users.

### Create an LDAP application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **LDAP Provider** as the provider type.
    - **Configure the Provider**: provide a name, select the bind flow, and note the **Base DN** because it will be required later.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Create a service account

1. Navigate to **Directory** > **Users** and click **New User**.
2. Select **Service Account**.
3. Set **Username** to `snipeit-user`.
4. Click **Next**.
5. Copy the generated app password from the confirmation screen because it will be required later.

### Assign LDAP search permissions

1. Navigate to **Directory** > **Roles** and click **Create**.
2. Create a role named `Snipe-IT LDAP search`.
3. Click the role that you created and open the **Users** tab.
4. Click **Add existing user**, select `snipeit-user`, and click **Assign**.
5. Navigate to **Applications** > **Providers**.
6. Click the LDAP provider that you created and open the **Permissions** tab.
7. Click **Assign Object Permissions**.
8. Select the role that you created, enable **Search full LDAP directory**, and click **Assign**.

### Create an LDAP outpost

1. Navigate to **Applications** > **Outposts** and click **New Outpost**.
2. Configure the following settings:
    - **Name**: enter a descriptive name, such as `Snipe-IT LDAP`.
    - **Type**: select **LDAP**.
    - **Applications**: select the LDAP application that you created.
3. Click **Create**.

### Create a SAML application and provider

<SAMLProvider20265Warning />

1. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **ACS URL** to `https://inventory.company/saml/acs`.
        - Set **Audience** to `https://inventory.company`.
        - Set **SLS URL** to `https://inventory.company/saml/sls`.
        - Under **Advanced protocol settings**, select any available **Signing Certificate** and enable **Sign assertions**.
        - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
2. Click **Submit** to save the new application and provider.

### Copy the SAML metadata URL

1. Navigate to **Applications** > **Providers**.
2. Click the SAML provider that you created.
3. Under **Related objects** > **Metadata**, click **Copy download URL**.

## Snipe-IT configuration

### Configure LDAP

1. Log in to Snipe-IT as an administrator.
2. Click the gear icon and select **LDAP**.
3. Configure the following settings:
    - **LDAP Integration**: enabled.
    - **LDAP Password Sync**: enabled.
    - **Active Directory**: disabled.
    - **LDAP Server**: `ldap://authentik.company`.
    - **LDAP Bind Username**: `cn=snipeit-user,ou=users,dc=ldap,dc=goauthentik,dc=io`.
    - **LDAP Bind Password**: enter the service account password from authentik.
    - **Base Bind DN**: `ou=users,dc=ldap,dc=goauthentik,dc=io`.
    - **LDAP Filter**: `&(objectClass=user)`.
    - **LDAP Username Field**: `mail`.
    - **LDAP Authentication query**: `mail=`.
    - **LDAP Last Name Field**: `sn`.
    - **LDAP First Name Field**: `givenname`.
    - **LDAP Email Field**: `mail`.
4. Click **Save**.
5. Click **Test LDAP Synchronization** to confirm that Snipe-IT can search the directory.
6. Enter an email address and password for an authentik user and click **Test LDAP Login** to confirm that Snipe-IT can authenticate through the LDAP provider.

If you changed the LDAP provider **Base DN** in authentik, replace `dc=ldap,dc=goauthentik,dc=io` in the Snipe-IT settings with your configured Base DN.

:::info LDAP attributes
Snipe-IT imports users only when the mapped first name and last name values are present. authentik maps the LDAP `sn` attribute to the user's full name by default. To send a separate last name, employee number, department, or other Snipe-IT user field, add those values as custom user attributes in authentik.
:::

### Synchronize users

1. In Snipe-IT, navigate to **People**.
2. Click **LDAP Sync**.
3. Select the location for the synchronized users.
4. Click **Synchronize**.

### Configure SAML

1. Click the gear icon and select **SAML**.
2. Configure the following settings:
    - **SAML enabled**: enabled.
    - **SAML IdP Metadata**: paste the SAML metadata URL from authentik.
    - **SAML Force Login**: enabled.
    - **SAML Single Log Out**: enabled.
3. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with Snipe-IT, open Snipe-IT, log out, and then log back in with SAML.

## Resources

- [Snipe-IT documentation - LDAP Sync & Login](https://snipe-it.readme.io/docs/ldap-sync-login)
- [Snipe-IT documentation - SAML](https://snipe-it.readme.io/docs/saml)
