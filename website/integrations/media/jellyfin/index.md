---
title: Integrate with Jellyfin
sidebar_label: Jellyfin
support_level: community
---

## What is Jellyfin?

> Jellyfin is a free and open source media management and streaming platform for movies, TV shows, and music.
>
> -- https://jellyfin.org

:::info
Jellyfin does not have any native external authentication support as of the writing of this page. Currently, there are two plugins for Jellyfin that provide external authentication, an OIDC plugin and an LDAP plugin.
:::

:::caution
An LDAP outpost must be deployed to use the Jellyfin LDAP plugin.
:::

## Preparation

The following placeholders are used in this guide:

- `jellyfin.company` is the FQDN of the Jellyfin installation.
- `authentik.company` is the FQDN of the authentik installation.
- `ldap.company` is the FQDN of the LDAP outpost.
- `dc=company,dc=com` is the Base DN of the LDAP outpost.
- `ldap_service_account` is the username of the LDAP service account.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## LDAP configuration

### authentik configuration

Follow the [LDAP provider setup](/docs/add-secure-apps/providers/ldap/create-ldap-provider/) to create the LDAP application, provider, service account, and outpost. Complete the [service account creation](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#create-a-service-account) and [LDAP search permission](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#assign-the-ldap-search-permission-to-the-service-account) steps for the account Jellyfin uses to connect to LDAP.

If access to the authentik LDAP application is restricted, allow the LDAP service account access via the application's [policy, group, or user bindings](/docs/add-secure-apps/applications/manage_apps/#use-bindings-to-control-access).

### Jellyfin configuration

1. Use the LDAP service account configured in authentik for Jellyfin's LDAP connection.
2. Navigate to your Jellyfin installation and log in with the administrator account or currently configured local admin.
3. Open the **Administrator dashboard** and go to the **Plugins** section.
4. Click **Catalog** at the top of the page, and locate the "LDAP Authentication Plugin".
5. Install the plugin. You may need to restart Jellyfin to finish installation.
6. Once finished, navigate back to the plugins section of the admin dashboard, click the three dots on the "LDAP-Auth Plugin" card, and click **Settings**.
7. Configure the LDAP Settings as follows:
    - `LDAP Server`: `ldap.company`
    - `LDAP Port`: 636
    - `Secure LDAP`: **Checked**
    - `StartTLS`: Unchecked
    - `Skip SSL/TLS Verification`:
        - If using a certificate issued by a certificate authority, Jellyfin trusts, leave this unchecked.
        - If you're using a self-signed certificate, check this box.
    - `Allow password change`: Unchecked
        - Since authentik already has a frontend for password resets, it's not necessary to include this in Jellyfin, especially since it requires the LDAP service account to have additional privileges.
    - `Password Reset URL`: Empty
    - `LDAP Bind User`: Set this to the LDAP service account DN. By default, the path will be `ou=users,dc=company,dc=com` so the value will be `cn=ldap_service_account,ou=users,dc=company,dc=com`.
    - `LDAP Bind User Password`: The password or token for the LDAP service account.
    - `LDAP Base DN for Searches`: the base DN for LDAP queries. To query all users, set this to `dc=company,dc=com`.
        - You can specify an OU if you divide your users up into different OUs and only want to query a specific OU.

At this point, click **Save and Test LDAP Server Settings**. If the settings are correct, you will see:
`Connect(Success); Bind(Success); Base Search (Found XY Entities)`

- `LDAP User Filter`: This is used to apply a user filter on which users are allowed to log in. **This must be set**
    - To allow all users: `(objectClass=user)`
    - To only allow users in a specific group: `(memberOf=cn=jellyfin_users,ou=groups,dc=company,dc=com)`
    - Good Docs on LDAP Filters: [atlassian.com](https://confluence.atlassian.com/kb/how-to-write-ldap-search-filters-792496933.html)
- `LDAP Admin Base DN`: All the users in this DN are automatically set as admins.
    - This can be left blank. Admins can be set manually outside this filter.
- `LDAP Admin Filter`: Similar to the user filter, but every matched user is set as admin.
    - This can be left blank. Admins can be set manually outside this filter.

At this point, click **Save and Test LDAP Filter Settings**. If the settings are correct, you will see:
`Found X user(s), Y admin(s)`

- `LDAP Attributes`: `uid, cn, mail, displayName`
- `Enable case Insensitive Username`: **Checked**

At this point, enter a username and click **Save Search Attribute Settings and Query User**. If the settings are correct, you will see:
`Found User: cn=test,ou=users,dc=company,dc=com`

- `Enabled User Creation`: **Checked**
- `LDAP Name Attribute`: `cn`
- `LDAP Password Attribute`: `userPassword`
- `Library Access`: Set this according to desired library access

1. Click "Save".
2. Log out, and log in with an LDAP user. Username **must** be used; logging in with email will not work.

## OIDC configuration

### authentik configuration

**Provider Settings**

In authentik under **Providers**, create an OAuth2/OpenID Provider with these settings:

- Name: `jellyfin`
- Redirect URI: `https://jellyfin.company/sso/OID/redirect/authentik`

Everything else is up to you, just make sure to grab the client ID and the client secret!

:::info
The last part of the URI is the name you use when making the provider in Jellyfin so make sure they are the same.
:::

**Application Settings**

Create an application that uses `jellyfin` provider. Optionally apply access restrictions to the application.

Set the launch URL to `https://jellyfin.company/sso/OID/start/authentik`

### Jellyfin configuration

1. Log in to Jellyfin with an administrator account and navigate to the **Admin Dashboard** by selecting your profile icon in the top-right corner, then clicking **Dashboard**.
2. Go to **Dashboard > Plugins > Repositories**.
3. Click the **+** in the top-left corner to add a new repository. Use the following URL and name it "SSO-Auth":

```
https://raw.githubusercontent.com/9p4/jellyfin-plugin-sso/manifest-release/manifest.json
```

4. Click the **Catalog** tab on top and install the SSO-Auth with the most recent version.
5. Restart the Jellyfin server.
6. Go back to the plugin tab.
7. Click the SSO-Auth plugin.
8. Fill out the Add / Update Provider Configuration:
    - Name of OID Provider: `authentik`
    - OID Endpoint: `https://authentik.company/application/o/jellyfin/.well-known/openid-configuration`
    - OpenID Client ID: ClientID from provider
    - OID Secret: Client Secret from provider
    - Enabled: **CHECKED**
    - Enable Authorization by Plugin: **CHECKED**

9. If you want to use the role claim then also fill out these:
    - Roles: roles to look for when authorizing access (should be done through authentik instead)
    - Admin Roles: roles to look for when giving administrator privilege
    - Role Claim: `groups`

10. Hit **Save** at the bottom.
11. On the left side now click the **General** under dashboard and go to **Branding**.
12. In the login disclaimer, put this code and make sure to change the URL at the top:

```
<form action="https://jellyfin.company/sso/OID/start/authentik">
  <button class="raised block emby-button button-submit">
    Sign in with SSO
  </button>
</form>
```

13. In the Custom CSS code also add this:

```
a.raised.emby-button {
    padding:0.9em 1em;
    color: inherit !important;
}

.disclaimerContainer{
    display: block;
}
```

14. Click **Save** at the bottom & restart the server.
15. When you are signed out you should now see a **Sign in with SSO** button.

:::info
If you have problems, check your logs under **Administration** > **Dashboard** > "logs". They will most likely be near the bottom with `Jellyfin.Plugin.SSO_Auth.` at the start of the lines you are looking for.
:::
