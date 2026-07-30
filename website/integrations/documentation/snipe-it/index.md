---
title: Integrate with Snipe-IT
sidebar_label: Snipe-IT
support_level: community
---

<<<<<<< HEAD
## What is Snipe-IT
=======
import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Snipe-IT?
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

> A free open source IT asset/license management system.
>
> -- https://snipeitapp.com

## Preparation

The following placeholders are used in this guide:

- `inventory.company` is the FQDN of the Snipe-IT installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

<<<<<<< HEAD
## authentik Configuration

### Step 1 - Service account
=======
:::warning HTTPS required
Configure Snipe-IT with an HTTPS `APP_URL` before you enable SAML. Snipe-IT generates its SAML entity ID, ACS URL, SLS URL, and metadata URL from that value.
:::

:::info Local login fallback
If SAML login is enabled and you need to use Snipe-IT's local login form, open `https://inventory.company/login?nosaml`.
:::

## authentik configuration

To support the integration of Snipe-IT with authentik, you need an LDAP application/provider pair, an LDAP bind service account, an LDAP outpost, and a SAML application/provider pair. LDAP sync creates the Snipe-IT users, and SAML authenticates those users.
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

### Create an LDAP application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **LDAP Provider** as the provider type.
    - **Configure the Provider**: provide a name, select the bind flow, and note the **Base DN** because it will be required later.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

<<<<<<< HEAD
:::note
If you didn't keep the password, you can copy it from _Directory/Tokens & App password_.
:::

### Step 2 - LDAP Provider

In authentik, create a LDAP Provider (under _Applications/Providers_) with these settings :

- Name : Snipe IT-LDAP
- Bind DN : `DC=ldap,DC=goauthentik,DC=io`
- Certificate : `authentik Self-signed Certificate`

### Step 3 - Application

In authentik, create an application (under _Resources/Applications_) with these settings :

- Name: Snipe IT-LDAP
- Slug: snipe-it-ldap
- Provider: Snipe IT-LDAP

### Step 4 - Outpost

In authentik, create an outpost (under _Applications/Outposts_) of type `LDAP` that uses the LDAP Application you created in _Step 3_.

- Name: LDAP
- Type: LDAP

## Snipe-IT LDAP Setup

Configure Snipe-IT LDAP settings by going to settings (he gear icon), and selecting `LDAP`

Change the following fields

- LDAP Integration: **ticked**
- LDAP Password Sync: **ticked**
- Active Directory : **unticked**
- LDAP Client-Side TLS Key: (taken from authentik)
- LDAP Server: `ldap://authentik.company`
- Use TLS : **unticked**
- LDAP SSL certificate validation : **ticked**
- Bind credentials:
    - LDAP Bind USername: `cn=snipeit-user,ou=users,dc=ldap,dc=goauthentik,dc=io`
    - LDAP Bind Password: `<snipeit-user password from step 2>`
- Base Bind DN: `ou=users,DC=ldap,DC=goauthentik,DC=io`
  :::note
  ou=users is the default OU for users. If you are using authentik's virtual groups, or have your users in a different organizational unit (ou), change accordingly.
  :::
- LDAP Filter: &(objectClass=user)
- Username Field: mail
  :::note
  Setting the Username field to mail is recommended in order to ensure the usernameisunique. See https://snipe-it.readme.io/docs/ldap-sync-login
  :::
- Allow unauthenticated bind: **unticked**
- Last Name: sn
- LDAP First Name: givenname
- LDAP AUthentication query: cn=
- LDAP Email: mail

:::note
authentik does not support other LDAP attributes like Employee Number, Department, etc out of the box. If you need these fields, you will need to setup custom attributes.
:::

Save your config, then click on Test LDAP Synchorization. This does not import any users, just verifies everything is working and the account can search the directory.

To test your settings, enter a username and password and click Test LDAP.

## Snipe-IT LDAP Sync

You must sync your LDAP database with Snipe-IT. Go to People on the sidebar menu.

- CLick `LDAP Sync`
- Select your Location
- Click Synchronize
  :::note
  Snipe-IT will only import users with both a first and last name set. You need to create user attributes with first and last names.
  :::

## authentik SAML Config

### Step 1

Create another application in authentik and note the slug you choose, as this will be used later. In the Admin Interface, go to Applications ->Providers. Create a SAML provider with the following parameters:

- ACS URL: `https://inventory.company/saml/acs`
- Issuer: `https://inventory.company`
- Service Provider Binding: `Post`
- Audience: `https://inventory.company`
- Signing certificate: Select any certificate you have.
- Property mappings: Select all Managed mappings.
- NamedID Property Mapping: authentik default SAML Mapping: Email
  :::note
  This is to match setting the username as **mail**. If you are using another field as the username, set it here.
  :::

### Step 2

After saving your new Application and Provider, go to _Applications/Providers_ and select your newly created Provider.

Either copy the information under SAML Metadata, or click the Download button under SAML Metadata

## Snipe-IT SAML Config

Configure Snipe-IT SAML settings by going to settings (he gear icon), and selecting `SAML`

- SAML enabled: **ticked**
- SAML IdP Metadata: (paste information copied in Step 2 above -or-
- Click `Select File`and select the file you downloaded in Step 2
- Attribute Mapping - Username: mail
- SAML Force Login: **ticked**
- SAML Single Log Out: **ticked**

All other field can be left blank.
=======
### Create a service account

1. Navigate to **Directory** > **Users** and click **New User**.
2. Select **Service Account**.
3. Set **Username** to `snipeit-user`.
4. Click **Next**.
5. Copy the generated app password from the confirmation screen because it will be required later.

If you configured bindings on the LDAP application, ensure that `snipeit-user` is allowed by those bindings so that Snipe-IT can bind to the LDAP provider.

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
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

## Additional Resources

- [Snipe-IT documentation - LDAP Sync & Login](https://snipe-it.readme.io/docs/ldap-sync-login)
- [Snipe-IT documentation - SAML](https://snipe-it.readme.io/docs/saml)
