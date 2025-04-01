---
title: Integrate with Calibre-Web
sidebar_label: Calibre-Web
support_level: community
---

## What is Calibre-Web

> Calibre-Web is a web app that offers an interface for browsing, reading, and downloading eBooks using a valid Calibre database.
>
> -- https://github.com/janeczku/calibre-web

## Preparation

The following placeholders are used in this guide:

- `calibreweb.company` is the FQDN of the Calibre-Web installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of _Calibre-Web_ with authentik, you need to create an application/provider pair and a correspdonding group in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.

- **Choose a Provider type**: select LDAP Provider as the provider type.

- **Configure the Provider**: provide a name (or accept the auto-provided name) and set the authorization flow to use for this provider.

- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Create a group in authentik

Create a group that will grant access to Calibre-Web.

1. Navigate to **Directory** > **Groups** and click **Create**.

- **Name**: provide a name (e.g. `Calibre-Web`).

2. Click **Create**.

### Add users to the group

Add the user that require access to the newly created group.

1. Navigate to **Directory** > **Groups** and click on the name of the group (e.g. `Calibre-Web`) that was just created.

2. Navigate to the **Users** tab and click **Add existing user**.

3. Click **+**.

4. Select the user that requires access and click **Add**.

5. Click **Add**.

## Calibre-Web configuration

1. Navigate to **Admin** > **Edit Basic Configuration** and click on **Feature Configuration** and set the following options:

- Login Type: `Use LDAP Authentication`
- LDAP Server: `<em>authentik.company</em>`
- LDAP Server Port: `389`
- LDAP Encryption: `None`
- LDAP Authentication: `Simple`
- LDAP Administrator Username: `cn=<em><authentik_administrator_username></em>,ou=users,dc=goauthentik,dc=io` (e.g. `cn=akadmin,ou=users,dc=goauthentik,dc=io`)
- LDAP Administrator Password: `<em><authentik_administrator_password></em>`
- LDAP Distinguished Name (DN): `dc=ldap,dc=goauthentik,dc=io`
- LDAP User Object Filter: `(&(objectclass=user)(cn=%s))`
- LDAP Server is OpenLDAP?: `true`
- LDAP Group Object Filter: `(&(objectclass=group)(cn=%s))`
- LDAP Group Name: `<em><group_name></em>` (e.g. `Calibre-Web`)
- LDAP Group Members Field: `member`
- LDAP Member User Filter Detection: `Autodetect`

2. Click **Save**.

3. Navigate to **Admin** and click **Import LDAP Users**

4. Once the user is imported from authentik, click **Edit Users** and give the user the desired permissions by checking the relevant checkboxes.

## Configuration verification

To confirm that authentik is properly configured with _Calibre-Web_, log out and log back in using the credentials of a user that is a member of the LDAP group (e.g. `Calibre-Web`).
