---
title: Integrate with Emby
sidebar_label: Emby
support_level: community
---

## What is Emby?

> Emby is a media management and streaming platform for movies, TV shows, and music that allows you to organize and stream your personal media collection.
>
> -- https://emby.media/

## Preparation

The following placeholders are used in this guide:

- `emby.company` is the FQDN of the Emby installation.
- `authentik.company` is the FQDN of the authentik installation.
- `ldap.company` is the FQDN of the LDAP outpost.
- `dc=company,dc=com` is the Base DN of the LDAP provider.

:::info Emby Premiere requirement
An [Emby Premiere](https://emby.media/premiere.html) subscription is required to use the official LDAP Authentication plugin.
:::

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Emby with authentik, you need to create an LDAP application/provider pair in authentik, create a service account, and expose the provider through an LDAP outpost.

### Create an LDAP application, provider, and outpost in authentik

Follow the [LDAP provider setup](/docs/add-secure-apps/providers/ldap/create-ldap-provider/) to create the LDAP application, provider, service account, and outpost.

Complete the [service account creation](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#create-a-service-account) and [LDAP search permission](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#assign-the-ldap-search-permission-to-the-service-account) steps for the account Emby uses to connect to LDAP.

When configuring the LDAP provider, set the following required configurations:

- **Base DN**: `dc=company,dc=com`
- **Certificate**: select the certificate that Emby should trust for LDAPS.
- **TLS Server Name**: `ldap.company`

If access to the authentik LDAP application is restricted, allow the LDAP service account access via the application's [policy, group, or user bindings](/docs/add-secure-apps/applications/manage_apps/#use-bindings-to-control-access).

### Create an Emby access group

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Groups**.
3. Click **Create**, set **Name** to `emby_users`, and click **Create**.
4. Open the new group, click the **Users** tab, and click **Add existing user** to add the users who should have access to Emby.

## Emby configuration

1. Access your Emby server and log in using the administrator account or the currently configured local administrator credentials.
2. Click the **cog icon** in the upper-right corner to access the dashboard settings.
3. Navigate to the **Plugins** section and click **Catalog** at the top of the page.
4. Find and install the **LDAP Authentication** plugin. Restart Emby if prompted to complete the installation.
5. After installation, return to the plugins section and click the **LDAP Authentication** plugin to open its settings.
6. Configure the LDAP settings as follows:
    - **LDAP server address**: `ldap.company`
    - **LDAP server Port number**: `636`
    - **Enable SSL**: checked
    - **SSL certificate thumbprint (SHA1)**: paste the SHA1 fingerprint of the certificate selected on the LDAP provider. This value is shown in authentik under **System** > **Certificates**.
    - **Bind DN**: `cn=ldap_service_account,ou=users,dc=company,dc=com`
    - **Bind credentials**: enter the password for the LDAP service account.
    - **User search base**: `dc=company,dc=com`
    - **User Search Filter**: `(&(sAMAccountName={0})(memberOf=cn=emby_users,ou=groups,dc=company,dc=com))`
        - To allow all users that the LDAP provider exposes, use `(&(objectClass=user)(sAMAccountName={0}))`.

7. Click **Save** to apply your configuration.

:::caution Administrator sign-in
Emby administrators sign in with Emby authentication instead of LDAP. Keep a local Emby administrator account available so you can access the server if LDAP is unavailable.
:::

## Configuration verification

To confirm that authentik is properly configured with Emby, open Emby, log out, and log back in using an authentik username and password. Logging in with an email address isn't supported, so use the username value from authentik.

If login fails, verify the LDAP search filter and check the Emby server logs for LDAP authentication errors.

## Resources

- [Emby Blog - Introducing LDAP support for Emby](https://emby.media/introducing-ldap-support-for-emby.html)
- [Emby Community - LDAP Configuration](https://emby.media/community/topic/75295-ldap-configuration/)
