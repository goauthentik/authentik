---
title: QNAP NAS
---

## What is QNAP NAS

> QNAP Systems, Inc. is a Taiwanese corporation that specializes in network-attached storage appliances used for file sharing, virtualization, storage management and surveillance applications.
>
> -- https://en.wikipedia.org/wiki/QNAP_Systems

Connecting a QNAP NAS to an LDAP Directory is a little bit special as it is **not** (well) documented what really is done behind the scenes of QNAP.

## Preparation

The following placeholders will be used:

-   `ldap.baseDN` is the Base DN you configure in the LDAP provider.
-   `ldap.domain` is (typically) a FQDN for your domain. Usually
    it is just the components of your base DN. For example, if
    `ldap.baseDN` is `dc=ldap,dc=goauthentik,dc=io` then the domain
    might be `ldap.goauthentik.io`.
-   `ldap.searchGroup` is the "Search Group" that can can see all
    users and groups in authentik.
-   `qnap.serviceAccount` is a service account created in authentik
-   `qnap.serviceAccountToken` is the service account token generated
    by authentik.

Create an LDAP Provider if you don't already have one setup.
This guide assumes you will be running with TLS. See the [ldap provider docs](../../../docs/providers/ldap) for setting up SSL on the authentik side.

Remember the `ldap.baseDN` you have configured for the provider as you'll
need it in the sssd configuration.

Create a new service account for all of your hosts to use to connect
to LDAP and perform searches. Make sure this service account is added
to `ldap.searchGroup`.

:::caution
It seems that QNAP LDAP client configuration has issues with too long password.
Max password length <= 66 characters.
:::

## Deployment

Create an outpost deployment for the provider you've created above, as described [here](../../../docs/outposts/). Deploy this Outpost either on the same host or a different host that your QNAP NAS can access.

The outpost will connect to authentik and configure itself.

## NAS Configuration

The procedure is a two step setup:

1. QNAP Web UI: Used to setup and store initial data. Especially to store the encrypted bind password.
2. SSH config Edit: In order to adapt settings to be able to communicate with authentik LDAP Outpost.

:::note
The config edit is essential, as QNAP relies on certain not configurable things.
The search for users and groups relies on a fix filter for
`objectClass` in `posixAccount` or `posixGroup` classes.

Also by default the search scope is set to `one` (`singleLevel`), which can be
adapted in the config to `sub` (`wholeSubtree`).

### Sample LDAP request from QNAP

Default search for users

```text
Scope: 1 (singleLevel)
Deref Aliases: 0 (neverDerefAliases)
Size Limit: 0
Time Limit: 0
Types Only: false
Filter: (objectClass=posixAccount)
Attributes:
    uid
    userPassword
    uidNumber
    gidNumber
    cn
    homeDirectory
    loginShell
    gecos
    description
    objectClass
```

Default search for groups

```text
Scope: 1 (singleLevel)
Deref Aliases: 0 (neverDerefAliases)
Size Limit: 0
Time Limit: 0
Types Only: false
Filter: (objectClass=posixGroup)
Attributes:
    cn
    userPassword
    memberUid
    gidNumber
```

:::

### QNAP Web UI

Configure the following values and "Apply"
![qnap domain security](./qnap-ldap-configuration.png)

:::caution
With each save (Apply) in the UI the `/etc/config/nss_ldap.conf` will be overwritten with default values.
:::

:::note
The UI Configuration is necessary, as it will save the Password encrypted
in `/etc/config/nss_ldap.ensecret`.
:::

### SSH

Connect your QNAP NAS via SSH.
First stop the LDAP Service:

```bash
/sbin/setcfg LDAP Enable FALSE
/etc/init.d/ldap.sh stop
```

Edit the file at `/etc/config/nss_ldap.conf`:

```conf
host                        ${ldap.domain}
base                        ${ldap.baseDN}
uri                         ldaps://${ldap.domain}/
ssl                         on
rootbinddn                  cn=${qnap.serviceAccount},ou=users,${ldap.baseDN}
nss_schema                  rfc2307bis

# remap object classes to authentik ones
nss_map_objectclass         posixAccount    user
nss_map_objectclass         shadowAccount   user
nss_map_objectclass         posixGroup      group

# remap attributes
# uid to cn is essential otherwise only id usernames will occur
nss_map_attribute           uid             cn
# map displayName information into comments field
nss_map_attribute           gecos           displayName
# see https://ldapwiki.com/wiki/GroupOfUniqueNames%20vs%20groupOfNames
nss_map_attribute           uniqueMember    member

# configure scope per search filter
nss_base_passwd             ou=users,${ldap.baseDN}?one
nss_base_shadow             ou=users,${ldap.baseDN}?one
nss_base_group              ou=groups,${ldap.baseDN}?one

tls_checkpeer               no
referrals                   no
bind_policy                 soft
timelimit                   120
tls_ciphers                 EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:!MD5
nss_initgroups_ignoreusers  admin,akadmin
```

Now start the LDAP Service:

```bash
/sbin/setcfg LDAP Enable TRUE
/etc/init.d/ldap.sh start
```

To see if connection is working, type

```bash
# list users
$ getent passwd
```

The output should list local users and authentik accounts.

```bash
# list groups
$ getent group
```

The output should list local and authentik groups.
