---
title: Integrate with Emby
sidebar_label: Emby
support_level: community
---

## What is Emby

> Emby is a media management and streaming platform for movies, TV shows, and music that allows you to organize and stream your personal media collection.
>
> -- https://emby.media/

:::note
An [Emby Premiere](https://emby.media/premiere.html) subscription is required for LDAP authentication to work via the official plugin.
:::

## Preparation

The following placeholders are used in this guide:

- `emby.company` is the FQDN of your Emby installation.
- `authentik.company` is the FQDN of your authentik installation.
- `ldap.company` is the FQDN of your LDAP outpost.
- `dc=company,dc=com` is the Base DN of your LDAP provider.
- `ldap_service_account` is the name of the Service Account used for LDAP binding.
- `emby_users` is the name of the authentik group containing users who should have access to Emby.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

### LDAP Outpost Setup

Emby requires an LDAP outpost to authenticate users. Follow the [LDAP outpost documentation](/docs/add-secure-apps/outposts/) to create and configure an LDAP outpost for your environment.

### Service account creation

Create a dedicated service account for Emby LDAP authentication by following the ["Creating a service account" documentation](/docs/sys-mgmt/service-accounts). Once created, generate and copy the token for use in the Emby configuration.

## Emby configuration

1. Access your Emby server and log in using the administrator account or the currently configured local administrator credentials.
2. Click the **cog icon** (settings) located at the top right corner of the screen to access the dashboard settings.
3. Navigate to the **Plugins** section and click **Catalog** at the top of the page.
4. Locate and select the "LDAP Authentication" plugin.
5. Install the plugin. You may need to restart Emby to complete the installation.
6. After installation, return to the plugins section of the admin dashboard and click on the "LDAP Authentication" plugin icon to open its settings.
7. Configure the LDAP Settings as follows:
    - **LDAP server address**: `ldap.company`
    - **LDAP server Port number**: `636`
    - **Enable SSL**: Checked
    - **SSL certificate thumbprint (SHA1)**:
        - Paste the SHA1 Fingerprint of your LDAP outpost certificate. This can be found in your authentik instance under **System** > **Certificates**.
    - **Bind DN**: `cn=ldap_service_account,ou=users,dc=company,dc=com`
    - **Bind credentials**: Enter the token you copied when creating your service account.
    - **User search base**: The base DN for LDAP queries. To query all users, set this to `dc=company,dc=com`. You can also specify an Organizational Unit (OU) if you organize your users into different OUs and want to query only a specific one, for example: `ou=employees,dc=company,dc=com`
    - **User Search Filter**: This setting determines which users are allowed to log in:
        - **Allowing All Users**: `(&(objectClass=user)(cn={0}))` permits all users to log in.
        - **Allowing Specific Group Members**: `(&(objectClass=user)(memberOf=cn=emby_users,ou=groups,dc=company,dc=com)(cn={0}))` restricts access to members of the specified group.

8. Click **Save** to apply your configuration.

## Configuration Verification

Log out of Emby and attempt to log back in using your LDAP credentials from authentik. Logging in with an email address isn't supported, therefore use your **username**.

:::tip Troubleshooting
If you encounter login issues, verify your LDAP search filter configuration and check the Emby server logs for authentication errors. You can also test your LDAP configuration using ldapsearch as described in the [authentik LDAP troubleshooting documentation](/docs/add-secure-apps/providers/ldap/generic_setup).
:::
