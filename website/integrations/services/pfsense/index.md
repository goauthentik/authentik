---
title: pfSense
---

## What is pfSense

From https://www.pfsense.org/

:::note
The pfSense project is a free network firewall distribution, based on the FreeBSD operating system with a custom kernel and including third party free software packages for additional functionality.
:::

:::note
This is based on authentik 2022.3.31 and pfSense 2.6.0-amd64
:::

## Preparation

The following placeholders will be used:

- `authentik.company` is the FQDN of authentik.
- `pfsense-user` is the name of the authentik Service account we'll create.
- `DC=ldap,DC=goauthentik,DC=io` is the Base DN of the LDAP Provider (default)


### Step 1

In authentik, create a service account (under _Directory/Users_) for pfSense to use as the LDAP Binder and take note of the password generated.

In this example, we'll use `pfsense-user` as the Service account's username

:::note
If you didn't keep the password, you can copy it from _Directory/Tokens & App password_.
:::


### Step 2

In authentik, create a LDAP Provider (under _Applications/Providers_) with these settings :
- Name : LDAP
- Bind DN : `DC=ldap,DC=goauthentik,DC=io`
- Certificate : `self-signed`

### Step 3

In authentik, create an application (under _Resources/Applications_) with these settings :

- Name: LDAP
- Slug: ldap
- Provider: LDAP

### Step 4

In authentik, create an outpost (under _Applications/Outposts_) of type `LDAP` that uses the LDAP Application you created in _Step 3_.

- Name: LDAP
- Type: LDAP

## pfSense Setup

### Unsecure setup (without SSL)

:::caution
This set up should only be used for testing purpose, because passwords will be sent in clear text to authentik.  
:::

Add your authentik LDAP server to pfSense by going to your pfSense Web UI and clicking the `+ Add` under _System/User Manager/Authentication Servers_.

Change the following fields

- Descriptive name: LDAP authentik
- Hostname or IP address: `authentik.company`
- Transport: Standard TCP
- Base DN: `DC=ldap,DC=goauthentik,DC=io`
- Authentication containers: `OU=users,DC=ldap,DC=goauthentik,DC=io`
- Bind anonymous: **unticked**
- Bind credentials:
  - User DN: `cn=pfsense-user,ou=users,dc=ldap,dc=goauthentik,dc=io`
  - Password: `<pfsense-user password from step 2>`
- Extended Query: &(objectClass=user)
- Allow unauthenticated bind: **unticked**


## Notes

:::tip
Secure LDAP more by creating a group for your `DN Bind` users and restricting the `Search group` of the LDAP Provider to them.
:::