---
title: Integrate with QNAP NAS
sidebar_label: QNAP NAS
support_level: community
---

## What is QNAP NAS?

> QNAP designs and delivers network-attached storage, video surveillance, and networking solutions.
>
> -- https://www.qnap.com/

## Preparation

The following placeholders are used in this guide:

- `ldap.baseDN` is the base DN configured in the authentik LDAP provider.
- `ldap.domain` is the FQDN that resolves to the authentik LDAP outpost. This is commonly derived from the base DN. For example, if `ldap.baseDN` is `dc=ldap,dc=goauthentik,dc=io`, then `ldap.domain` might be `ldap.goauthentik.io`.
- `qnap.serviceAccount` is the authentik service account that QNAP NAS uses to bind to LDAP.
- `qnap.serviceAccountPassword` is the app password generated for the service account by authentik.

Connecting a QNAP NAS to authentik LDAP requires a two-step service configuration. First, use the QNAP web interface to store the encrypted bind password. Then, edit the generated LDAP configuration over SSH so QNAP can search authentik's LDAP structure.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning Password length
The QNAP LDAP client configuration has issues with passwords that are longer than 66 characters. Use a service account app password that is 66 characters or shorter.
:::

## authentik configuration

To support the integration of QNAP NAS with authentik, you need an LDAP application and provider, a service account with LDAP search permissions, and an LDAP outpost.

### Create the LDAP resources

1. Follow the [LDAP provider setup](/docs/add-secure-apps/providers/ldap/create-ldap-provider/) to create or reuse the LDAP application and provider, create a service account, assign the LDAP search permission, and create an LDAP outpost.
2. Use `qnap.serviceAccount` as the service account username and copy its generated app password as `qnap.serviceAccountPassword`.
3. Note the provider's **Base DN** value as `ldap.baseDN`.
4. Open the LDAP application's **Policy / Group / User Bindings** tab and bind `qnap.serviceAccount` and any users or groups that should be able to authenticate to QNAP NAS.
5. Ensure that the LDAP application is selected on the outpost and deploy the outpost where the QNAP NAS can reach it as `ldap.domain`.

## QNAP NAS configuration

### Configure LDAP in the web interface

1. Log in to the QNAP web interface as an administrator.
2. Navigate to **Control Panel** > **Privilege** > **Domain Security**.
3. Select **LDAP authentication**.
4. Configure the LDAP settings for your environment, using `ldap.domain`, `ldap.baseDN`, `qnap.serviceAccount`, and `qnap.serviceAccountPassword`.
5. Click **Apply**.

![QNAP domain security LDAP configuration](./qnap-ldap-configuration.png)

:::warning Configuration overwrite
Each time you click **Apply** in the QNAP LDAP web interface, QNAP overwrites `/etc/config/nss_ldap.conf` with generated values. Repeat the SSH changes below after saving LDAP settings in the web interface.
:::

The web interface step is required because QNAP stores the encrypted bind password in `/etc/config/nss_ldap.ensecret`.

### Update the LDAP configuration over SSH

QNAP searches users and groups with fixed filters for the `posixAccount` and `posixGroup` object classes. It also uses a single-level search scope unless the generated configuration is changed. The configuration below maps those object classes to authentik objects and keeps the search bases explicit.

Connect to the QNAP NAS over SSH and stop the LDAP service:

```bash
/sbin/setcfg LDAP Enable FALSE
/etc/init.d/ldap.sh stop
```

Edit `/etc/config/nss_ldap.conf`:

```ini title="/etc/config/nss_ldap.conf"
host                        ${ldap.domain}
base                        ${ldap.baseDN}
uri                         ldaps://${ldap.domain}/
ssl                         on
rootbinddn                  cn=${qnap.serviceAccount},ou=users,${ldap.baseDN}
nss_schema                  rfc2307bis

nss_map_objectclass         posixAccount    user
nss_map_objectclass         shadowAccount   user
nss_map_objectclass         posixGroup      group

nss_map_attribute           uid             cn
nss_map_attribute           gecos           displayName
nss_map_attribute           uniqueMember    member

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

The configuration remaps QNAP's expected `posixAccount` and `posixGroup` object classes to authentik's `user` and `group` object classes. It also maps `uid` to `cn` so QNAP displays authentik usernames instead of internal IDs.

Start the LDAP service:

```bash
/sbin/setcfg LDAP Enable TRUE
/etc/init.d/ldap.sh start
```

## Configuration verification

To confirm that authentik is properly configured with QNAP NAS, connect to the NAS over SSH and list users and groups:

```bash
getent passwd
getent group
```

The output should include local QNAP entries and entries from authentik.

## Resources

- [QNAP tutorial: connecting a QNAP NAS to an LDAP directory](https://www.qnap.com/en/how-to/tutorial/article/connecting-a-qnap-nas-to-an-ldap-directory)
