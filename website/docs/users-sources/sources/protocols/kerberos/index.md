---
title: Kerberos
authentik_preview: true
authentik_version: "2024.10"
---

This source allows users to enroll themselves with an existing Kerberos identity.

## Preparation

The following placeholders are used in this guide:

- `REALM.COMPANY` is the Kerberos realm.
- `authentik.company` is the FQDN of the authentik install.

Examples are shown for an MIT Krb5 KDC system; you might need to adapt them for you Kerberos installation.

There are three ways to use the Kerberos source:

- As a password backend, where users can log in to authentik with their Kerberos password.
- As a directory source, where users are synced from the KDC.
- With SPNEGO, where users can log in to authentik with their [browser](./browser.md) and their Kerberos credentials.

You can choose to use one or several of those methods.

## Common settings

In the authentik Admin interface, under **Directory** -> **Federation and Social login**, create a new source of type Kerberos with these settings:

- Name: a value of your choosing. This name is shown to users if you use the SPNEGO login method.
- Slug: `kerberos`
- Realm: `REALM.COMPANY`
- Kerberos 5 configuration: If you need to override the default Kerberos configuration, you can do it here. See [man krb5.conf(5)](https://web.mit.edu/kerberos/krb5-latest/doc/admin/conf_files/krb5_conf.html) for the expected format.
- User matching mode: define how Kerberos users get matched to authentik users.
- Group matching mode: define how Kerberos groups (specified via property mappings) get matched to authentik groups.
- User property mappings and group property mappings: see [Source property mappings](../../property-mappings/index.md) and the section below for details.

## Password backend

No extra configuration is required. Simply select the Kerberos backend in the password stage of your flow.

Note that this only works on users that have been linked to this source, i.e. they must have been created via sync or via SPNEGO.

## Sync

The sync process uses the [Kerberos V5 administration system](https://web.mit.edu/kerberos/krb5-latest/doc/admin/database.html) to list users. Your KDC must support it to sync users with this source.

You need to create both a principal (a unique identity that represents a user or service in a Kerberos network) for authentik and a keytab file:

```bash
$ kadmin
> add_principal authentik/admin@REALM.COMPANY
> ktadd -k /tmp/authentik.keytab authentik/admin@REALM.COMPANY
> exit
$ cat /tmp/authentik.keytab | base64
$ rm /tmp/authentik.keytab
```

In authentik, configure these extra options:

- Sync users: enable it
- Sync principal: `authentik/admin@REALM.COMPANY`
- Sync keytab: the base64-encoded keytab created above.

If you do not wish to use a keytab, you can also configure authentik to authenticate using a password, or an existing credentials cache.

## SPNEGO

You need to create both a principal (a unique identity that represents a user or service in a Kerberos network) for authentik and a keytab file:

```bash
$ kadmin
> add_principal HTTP/authentik.company@REALM.COMPANY
> ktadd -k /tmp/authentik.keytab HTTP/authentik.company@REALM.COMPANY
> exit
$ cat /tmp/authentik.keytab | base64
$ rm /tmp/authentik.keytab
```

In authentik, configure these extra options:

- SPNEGO keytab: the base64-encoded keytab created above.

If you do not wish to use a keytab, you can also configure authentik to use an existing credentials cache.

You can also override the SPNEGO server name if needed.

You might need to configure your web browser to allow SPNEGO. Check out [our documentation](./browser.md) on how to do so. You can now login to authentik using SPNEGO.

### Custom server name

If your authentik instance is accessed from multiple domains, you might want to force the use of a specific server name. You can do so with the **Custom server name** option. The value must be in the form of `HTTP@authentik.company`.

If not specified, the server name defaults to trying out all entries in the keytab/credentials cache until a valid server name is found.

## Extra settings

There are some extra settings you can configure:

- Update internal password on login: when a user logs in to authentik using the Kerberos source as a password backend, their internal authentik password will be updated to match the one from Kerberos.
- Use password writeback: when a user changes their password in authentik, their Kerberos password is automatically updated to match the one from authentik. This is only available if synchronization is configured.

## Kerberos source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work with external sources.

By default, authentik ships with [pre-configured mappings](#built-in-property-mappings) for the most common Kerberos setups. These mappings can be found on the Kerberos Source Configuration page in the Admin interface.

### Built-in property mappings

Kerberos property mappings are used when you define a Kerberos source. These mappings define which Kerberos property maps to which authentik property. By default, the following mappings are created:

- authentik default Kerberos User Mapping: Add realm as group
  The realm of the user will be added as a group for that user.
- authentik default Kerberos User Mapping: Ignore other realms
  Realms other than the one configured on the source are ignored, and log in is not allowed.
- authentik default Kerberos User Mapping: Ignore system principals
  System principals such as `K/M` or `kadmin/admin` are ignored.
- authentik default Kerberos User Mapping: Multipart principals as service accounts
  Multipart principals (for example: `HTTP/authentik.company`) have their user type set to **service account**.

These property mappings are configured with the most common Kerberos setups.

### Expression data

The following variable is available to Kerberos source property mappings:

- `principal`: a Python string containing the Kerberos principal. For example `alice@REALM.COMPANY` or `HTTP/authentik.company@REALM.COMPANY`.

When the property mapping is invoked from a SPNEGO context, the following variable is also available:

- `spnego_info`: a Python dictionary with the following keys:
    - `initiator_name`: the name of the initiator of the GSSAPI security context
    - `target_name`: the name of the target of the GSSAPI security context
    - `mech`: the GSSAPI mechanism used. Should always be Kerberos
    - `actual_flags`: the flags set on the GSSAPI security context

When the property mapping is invoked from a synchronization context, the following variable is also available:

- `principal_obj`: a [`Principal`](https://kadmin-rs.readthedocs.io/latest/kadmin.html#kadmin.Principal) object retrieved from the KAdmin API

### Additional expression semantics

If you need to skip synchronization for a specific object, you can raise the `SkipObject` exception. To do so, create or modify your Kerberos property mapping to use an expression to define the object to skip.

**Example:**

```python
localpart, realm = principal.rsplit("@", 1)
if localpart == "username":
    raise SkipObject
```

## Troubleshooting

You can start authentik with the `KRB5_TRACE=/dev/stderr` environment variable for Kerberos to print errors in the logs.
