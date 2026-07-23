---
title: Integrate with The Lounge
sidebar_label: The Lounge
support_level: community
---

## What is The Lounge?

> The Lounge is a modern, web-based IRC client that keeps users connected to IRC servers even when they are offline.
>
> -- https://thelounge.chat/

## Preparation

The following placeholders are used in this guide:

- `ldap.company` is the FQDN of the authentik LDAP outpost.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of The Lounge with authentik, you need to create an LDAP application/provider pair, a service account, and an LDAP outpost in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **LDAP Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the bind flow to use for this provider, and note the **Base DN** because it will be required later.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Create a service account and LDAP outpost

After creating the application/provider pair, follow the LDAP provider setup to create a [service account](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#create-a-service-account), assign the [LDAP search permission](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#assign-the-ldap-search-permission-to-the-service-account) to the service account, and [create an LDAP outpost](/docs/add-secure-apps/providers/ldap/create-ldap-provider/#create-an-ldap-outpost) for this LDAP provider.

Use a descriptive service account name such as `the-lounge-ldap`, and note the service account's full Bind DN and password. The Lounge uses this account to search for a matching user DN before binding as that user.

If you configure application bindings, ensure that the LDAP bind service account and the users who should authenticate to The Lounge have access to the application.

## The Lounge configuration

The Lounge uses LDAP authentication only when it runs in private mode.

In `config.js`, set the following values in the `ldap` object:

```js title="config.js"
ldap: {
    enable: true,
    url: "ldap://ldap.company:389",
    primaryKey: "cn",
    searchDN: {
        rootDN: "cn=the-lounge-ldap,ou=users,DC=ldap,DC=goauthentik,DC=io",
        rootPassword: "<ldap_bind_password>",
        filter: "(objectClass=user)",
        base: "<ldap_base_dn>",
    },
},
```

To restrict access to members of a specific authentik group, set `filter` to the following value:

```js title="config.js"
filter: "(&(objectClass=user)(memberOf=cn=<group_name>,ou=groups,<ldap_base_dn>))",
```

Save `config.js` and restart The Lounge.

## Configuration verification

To confirm that authentik is properly configured with The Lounge, open The Lounge and log in with an authentik user's username and password.

## Resources

- [The Lounge documentation - Configuration](https://thelounge.chat/docs/configuration#ldap-support)
- [The Lounge source - LDAP authentication](https://github.com/thelounge/thelounge/blob/master/server/plugins/auth/ldap.ts)
