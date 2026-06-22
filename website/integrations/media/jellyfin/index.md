---
title: Integrate with Jellyfin
sidebar_label: Jellyfin
support_level: community
---

## What is Jellyfin?

> Jellyfin is a free and open source media management and streaming platform for movies, TV shows, and music.
>
> -- https://jellyfin.org

:::info External authentication support
Jellyfin does not include native external authentication support. This guide uses the Jellyfin LDAP Authentication plugin with an authentik LDAP provider and outpost.
:::

## Preparation

The following placeholders are used in this guide:

- `jellyfin.company` is the FQDN of the Jellyfin installation.
- `authentik.company` is the FQDN of the authentik installation.
- `ldap.company` is the FQDN of the LDAP outpost.
- `dc=company,dc=com` is the Base DN of the LDAP provider.
- `ldap_service_account` is the username of the LDAP service account.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Jellyfin with authentik, you need to create an LDAP application/provider pair, deploy an LDAP outpost, and create a service account for Jellyfin.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **LDAP Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and set the following required configuration.
        - **Base DN**: `dc=company,dc=com`
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure the LDAP outpost

Jellyfin requires an LDAP outpost to authenticate users against authentik. Follow the [LDAP provider setup](/docs/add-secure-apps/providers/ldap/create-ldap-provider/) to create or update the LDAP outpost for your environment.

After the outpost is created, add the Jellyfin LDAP application to it:

1. From the authentik Admin interface, navigate to **Applications** > **Outposts** and click the **Edit** icon next to your LDAP outpost.
2. From the **Available Applications** list, select the Jellyfin LDAP application and move it to the selected applications list.
3. Click **Update**.

### Create the LDAP service account

Create a dedicated service account for Jellyfin by following the [service account creation](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#create-a-service-account) and [LDAP search permission](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#assign-the-ldap-search-permission-to-the-service-account) steps in the LDAP provider documentation.

Use the service account's DN and token in the Jellyfin LDAP plugin configuration. With the placeholders from this guide, the service account DN is:

```text
cn=ldap_service_account,ou=users,dc=company,dc=com
```

If access to the authentik LDAP application is restricted, allow the LDAP service account access via the application's [policy, group, or user bindings](/docs/add-secure-apps/applications/manage_apps/#use-bindings-to-control-access).

### Create an access group

Create groups that grant user and administrator access to Jellyfin.

1. Navigate to **Directory** > **Groups** and click **Create**.
2. Set **Name** to a group name such as `jellyfin_users`.
3. Click **Create**.
4. Open the group, select the **Users** tab, and add the users who should have access to Jellyfin.
5. Repeat these steps with a group name such as `jellyfin_admins` if you want LDAP group membership to grant Jellyfin administrator access.

## Jellyfin configuration

1. Navigate to your Jellyfin installation and log in with the administrator account or currently configured local administrator.
2. Open the **Administrator dashboard** by selecting your profile icon in the top-right corner, then clicking **Dashboard**.
3. Navigate to **Plugins** > **Catalog** and install the **LDAP Authentication** plugin.
4. Restart Jellyfin if prompted.
5. Return to **Plugins**, click the three dots on the **LDAP-Auth Plugin** card, and click **Settings**.
6. Under **LDAP Server Settings**, configure the following settings:
    - **LDAP Server**: `ldap.company`
    - **LDAP Port**: `636`
    - **Secure LDAP**: enabled
    - **LDAP Bind User**: `cn=ldap_service_account,ou=users,dc=company,dc=com`
    - **LDAP Bind User Password**: enter the token for the LDAP service account.
    - **LDAP Base DN for searches**: `dc=company,dc=com`

7. If the LDAP outpost uses a certificate that Jellyfin does not trust, either configure **LDAP Root CA Path** with the certificate authority bundle or enable **Skip SSL/TLS Verification**.
8. Click **Save and Test LDAP Server Settings**. If the settings are correct, Jellyfin shows successful connect, bind, and base search results.
9. Under **LDAP User Settings**, configure the following settings:
    - **LDAP Search Filter**: `(memberOf=cn=jellyfin_users,ou=groups,dc=company,dc=com)`
    - **LDAP Search Attributes**: `uid, cn, mail, displayName`
    - **LDAP Uid Attribute**: `uid`
    - **LDAP Username Attribute**: `cn`

10. To grant Jellyfin administrator access through LDAP, set **LDAP Admin Filter** to `(memberOf=cn=jellyfin_admins,ou=groups,dc=company,dc=com)`. If you leave this empty, configure Jellyfin administrator access manually.
11. Click **Save and Test LDAP Filter Settings**. If the settings are correct, Jellyfin shows the number of matching users and administrators.
12. Enter a username in **Test Login Name**, then click **Save Search Attribute Settings and Query User** to confirm that Jellyfin can find the user.
13. Under **Jellyfin User Settings**, configure the following settings:
    - **Enable User Creation**: enabled
    - **Library Access**: select the libraries that new LDAP users can access.

14. Click **Save**.
15. Restart Jellyfin.

## Configuration verification

To confirm that authentik is properly configured with Jellyfin, log out of Jellyfin and log back in with an LDAP user from authentik. Use the user's username; logging in with an email address is not supported by this configuration.

If the login does not succeed, open **Administration** > **Dashboard** > **Logs** in Jellyfin and review the LDAP plugin log entries near the bottom of the newest log file.

## Resources

- [Jellyfin LDAP Authentication plugin](https://github.com/jellyfin/jellyfin-plugin-ldapauth)
- [Jellyfin plugin installation documentation](https://jellyfin.org/docs/general/server/plugins/#installing)
