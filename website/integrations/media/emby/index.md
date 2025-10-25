---
title: Integrate with Emby
sidebar_label: Emby
support_level: community
---

## What is Emby

> Emby is a media management and streaming platform for movies, TV shows, and music that allows you to organize and stream your personal media collection.
>
> -- https://emby.media/

:::info
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

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

### LDAP provider configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **LDAP Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name) and the authorization flow to use for this provider.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### LDAP outpost setup

Emby requires an LDAP outpost to authenticate users. Follow the [LDAP outpost documentation](/docs/add-secure-apps/outposts/) to create and configure an LDAP outpost for your environment.

### Add application to outpost

1. From the authentik Admin interface, navigate to **Applications** > **Outposts** and click the **Edit** icon next to your LDAP outpost.
2. Then, from the **Available Applications** list, select your new application/provider pair and click the single right arrow to move it to the selected list.
3. Click **Update**.

### Service account creation

Create a dedicated service account for Emby LDAP authentication by following the ["Creating a service account" documentation](/docs/sys-mgmt/service-accounts). Once created, generate and copy the token for use in the Emby configuration.
Create a dedicated service account for Emby LDAP authentication by following the instructions in ["Creating a service account" documentation](/docs/sys-mgmt/service-accounts). After the service account is created, generate and copy the token from the account; the token is required for the Emby configuration.

### Group creation

1. Log in to the authentik Admin interface as an administrator and navigate to **Directory** > **Groups**.
2. Click **Create** to add a new group, then set the **Name** field to `emby_users` and click **Create**.
3. Then, click on the newly created `emby_users` group and click **Add existing user** to assign users who should have access to Emby by navigating to the **Users** tab.

## Emby configuration

1. Access your Emby server and log in using the administrator account or the currently configured local administrator credentials.
2. Click the **cog icon** (settings) located at the top right corner of the screen to access the dashboard settings.
3. Navigate to the **Plugins** section and click **Catalog** at the top of the page.
4. Find and install the "LDAP Authentication" plugin. Restart Emby if prompted to complete the installation.
5. After installation, return to the plugins section and click on the "LDAP Authentication" plugin to open its settings.
6. Configure the LDAP Settings as follows:
    - **LDAP server address**: `ldap.company`
    - **LDAP server Port number**: `636`
    - **Enable SSL**: Checked
    - **SSL certificate thumbprint (SHA1)**: Paste the SHA1 Fingerprint of your LDAP outpost certificate. This can be found in your authentik instance under **System** > **Certificates**.
    - **Bind DN**: `cn=ldap_service_account,ou=users,dc=company,dc=com`
    - **Bind credentials**: Enter the token you copied when creating your service account.
    - **User search base**: The base DN for LDAP queries. To query all users, set this to `dc=company,dc=com`. You can also specify an Organizational Unit (OU) if you organize your users into different OUs and want to query only a specific one, for example: `ou=employees,dc=company,dc=com`
    - **User Search Filter**: This setting determines which users are allowed to log in:
        - **Allowing All Users**: `(&(objectClass=user)(cn={0}))` permits all users to log in.
        - **Allowing Specific Group Members**: `(&(objectClass=user)(memberOf=cn=emby_users,ou=groups,dc=company,dc=com)(cn={0}))` restricts access to members of the specified group.

7. Click **Save** to apply your configuration.

## Configuration Verification

Log out of Emby and attempt to log back in using your LDAP credentials from authentik. Logging in with an email address isn't supported, therefore use your **username**.

## Troubleshooting

If you encounter login issues, verify your LDAP search filter configuration and check the Emby server logs for authentication errors. You can also test your LDAP configuration using ldapsearch as described in the [authentik LDAP troubleshooting documentation](/docs/add-secure-apps/providers/ldap/generic_setup).

## Resources

- [Emby Blog - Introducing LDAP support for Emby](https://emby.media/introducing-ldap-support-for-emby.html)
- [Emby Community - How to set up the LDAP plug-in correctly?](https://emby.media/community/index.php?/topic/106525-how-to-set-up-the-ldap-plug-in-correctly/)
