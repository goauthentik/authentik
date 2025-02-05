---
title: Integrate with The Lounge
sidebar_label: The Lounge
---

# Integrate with The Lounge

<span class="badge badge--secondary">Support level: Community</span>

## What is The Lounge

> The Lounge is a modern, web-based IRC (Internet Relay Chat) client that allows users to stay connected to IRC servers even when offline.
>
> -- https://thelounge.chat/

:::note
This guide assumes you already deployed an LDAP Provider, if not check [here](https://docs.goauthentik.io/docs/add-secure-apps/providers/ldap/generic_setup).
If you made any changes, e.g. using a different name for the user, make sure to apply them here as well.
:::

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `dc=company,dc=com` the Base DN of the LDAP outpost. If you followed the LDAP provider guide this is: `dc=goauthentik,dc=io`
- `ldap_bind_user` the username of the desired LDAP Bind User. If you followed the LDAP provider guide this is: `ldapservice`

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## LDAP Configuration

### authentik Configuration

Follow the [instructions](https://docs.goauthentik.io/docs/add-secure-apps/outposts/#create-and-configure-an-outpost) to create an LDAP outpost and configure access via the outpost. No additional authentik configuration needs to be configured.

### The Lounge configuration

In the `config.js` file find the `ldap` section and make the following changes:

1. Set `enable` to `true`
2. Set `url` to `ldap://authentik.company`
3. Set `primaryKey` to `cn`
4. In the `searchDN` section make the following changes:
    1. Set `rootDN` to `cn=ldap_bind_user,ou=users,dc=company,dc=com`
    2. Set `rootPassword` to the password you have given to the `ldap_bind_user`
    3. Set `filter` to `(&(objectClass=user)`
        1. Alternatively, if you want to restrict access by group, you can set it to: `(&(objectClass=user)(memberOf=cn=group_name,ou=groups,dc=ldap,dc=company,dc=com))`
    4. Set `base` to `dc=ldap,dc=company,dc=com`
5. Finally, save the `config.js` file and restart The Lounge. You should be able to log in via LDAP now, as long as a user with the same name exists.
