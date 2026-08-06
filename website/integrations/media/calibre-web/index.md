---
title: Integrate with Calibre-Web
sidebar_label: Calibre-Web
support_level: community
---

## What is Calibre-Web?

> Calibre-Web is a web app that offers an interface for browsing, reading, and downloading eBooks using a valid Calibre database.
>
> -- https://github.com/janeczku/calibre-web

## Preparation

The following placeholders are used in this guide:

- `calibreweb.company` is the FQDN of the Calibre-Web installation.
- `authentik.company` is the FQDN of the authentik installation.
- `ldap.company` is the FQDN of the authentik LDAP outpost.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Calibre-Web must be installed with its optional LDAP dependencies. If **Use LDAP Authentication** is not available as a login type, install the Calibre-Web LDAP dependencies and restart Calibre-Web before continuing.

## authentik configuration

To support the integration of Calibre-Web with authentik, you need to create an LDAP application/provider pair, an LDAP outpost, a service account with LDAP search permissions, and a group containing the users to import into Calibre-Web.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **LDAP Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the bind flow to use for this provider, and note the **Base DN** because it will be required later.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Create an LDAP outpost

Calibre-Web connects to authentik through an LDAP outpost.

1. Navigate to **Applications** > **Outposts** and click **New Outpost**.
2. Configure the outpost:
    - **Name**: provide a descriptive name.
    - **Type**: select **LDAP**.
    - **Integration**: select the integration that matches your deployment method.
    - **Applications**: select the Calibre-Web LDAP application.
3. Click **Create**.

Expose the LDAP outpost as `ldap.company` so Calibre-Web can reach it.

### Create a service account in authentik

Create a dedicated service account for Calibre-Web LDAP searches.

1. Navigate to **Directory** > **Users** and click **New User**.
2. Set **Username** to a descriptive value, such as `ldapservice`, then click **Create**.
3. Click the newly created service account.
4. Under **Recovery**, click **Set password**, provide a secure password, and click **Update password**. Copy this password because it will be required later.

For the default authentik LDAP Base DN, this service account's DN is `cn=<service_account_username>,ou=users,dc=ldap,dc=goauthentik,dc=io`.

### Grant LDAP search permissions

Calibre-Web needs the service account to search the LDAP directory when importing users.

1. Navigate to **Directory** > **Roles** and click **Create**.
2. Provide a name, such as `LDAP search`, and click **Create**.
3. Click the new role and open the **Users** tab.
4. Click **Add existing user**, select the service account, and click **Assign**.
5. Navigate to **Applications** > **Providers** and click the Calibre-Web LDAP provider.
6. Open the **Permissions** tab and click **Assign Object Permissions**.
7. Select the role, enable **Search full LDAP directory**, and click **Assign**.

### Create an LDAP import group

Create a group that contains the users to import into Calibre-Web.

1. Navigate to **Directory** > **Groups** and click **Create**.
2. Provide a name, such as `Calibre-Web`, and click **Create**.
3. Click the newly created group and open the **Users** tab.
4. Click **Add existing user**.
5. Select the users that should be imported into Calibre-Web and click **Add**.

Note the group name because it will be required later.

## Calibre-Web configuration

1. Log in to Calibre-Web as an administrator.
2. Navigate to **Admin** > **Edit Basic Configuration**, open **Feature Configuration**, and configure the following settings:
    - **Login Type**: `Use LDAP Authentication`
    - **LDAP Server Host Name or IP Address**: `ldap.company`
    - **LDAP Administrator Username**: `cn=<service_account_username>,ou=users,dc=ldap,dc=goauthentik,dc=io`
    - **LDAP Administrator Password**: enter the service account password from authentik.
    - **LDAP Distinguished Name (DN)**: `dc=ldap,dc=goauthentik,dc=io`
    - **LDAP User Object Filter**: `(&(objectclass=user)(cn=%s))`
    - **LDAP Group Object Filter**: `(&(objectclass=group)(cn=%s))`
    - **LDAP Group Name**: enter the authentik LDAP import group name, for example `Calibre-Web`.
    - **LDAP Group Members Field**: `member`
3. Click **Save**.

If you changed the LDAP provider **Base DN** in authentik, replace `dc=ldap,dc=goauthentik,dc=io` in the Calibre-Web settings with your configured Base DN.

After saving the LDAP settings, import users from authentik:

1. Navigate to **Admin** and click **Import LDAP Users**.
2. After the users are imported, click **Edit Users** and give each imported user the appropriate Calibre-Web permissions.

## Configuration verification

To confirm that authentik is properly configured with Calibre-Web, open Calibre-Web and log in as an imported user using their authentik credentials.

## Resources

- [Calibre-Web LDAP Login documentation](https://github.com/janeczku/calibre-web/wiki/LDAP-Login)
