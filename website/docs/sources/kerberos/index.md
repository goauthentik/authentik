---
title: SPNEGO
---

This source allows users to enroll themselves with an existing Kerberos identity.

## Preparation

The following placeholders will be used:

-   `REALM.COMPANY` is the Kerberos realm.
-   `authentik.company` is the FQDN of the authentik install.

Examples are shown for an MIT Krb5 KDC, you may need to adapt them for you Kerberos installation.

## Kerberos configuration

You need to create a principal for authentik and a keytab:

```bash
$ kadmin
> add_principal HTTP/authentik.company@REALM.COMPANY
> ktadd -k /tmp/authentik.keytab HTTP/authentik.company@REALM.COMPANY
> exit
$ cat /tmp/authentik.keytab | base64
```

Keep the base64-encoded keytab for later.

## authentik configuration

In the Admin interface, under **Directory** -> **Federation and Social login**, create a new source of type SPNEGO with these settings:

-   Name: a value of your choosing that will be shown to users
-   Slug: `kerberos`
-   Keytab: the keytab created above

## Finalizing

You may need to configure your web browser to allow SPNEGO. Check out [our documentation](./browser) on how to do so. You can now login to authentik using SPNEGO.

## Note on user linking

When editing the source, you can choose the **User matching mode**. For the SPNEGO source, the unique identifier will be the user principal, i.e. `alice@REALM.COMPANY`, the username will be `alice` and the email will be empty. You can enable **Guess email** under **Advanced protocol settings**, in which case the email would be `alice@realm.company`. This option does not perform any kind of validation, use with care.

## Advanced configuration

The following section is intended for advanced users with specific needs and showcases some exotic configurations.

### Custom Kerberos configuration

authentik bundles a sensible default Kerberos configuration which should work with most implementations. If you need to override that, you can mount your own `krb5.conf` in the authentik containers at `/etc/krb5.conf`.

### Custom server name

If your authentik instance is accessed from multiple domains, you may want to force the use of a specific server name. You can do so with this option. It must be in the form of `HTTP/domain@REALM`.

If not specified, this defaults to trying out all entries in the keytab/credentials cache until a valid server name is found.

### Mounted keytab

If you prefer to mount your keytab in the authentik containers instead of storing in the database, you can do so by specifying `FILE:/path/to/keytab` instead of the base64-encoded keytab. If the field is left empty, authentik will use the default keytab path configuration method used by MIT Krb5.

### Custom credentials cache

By default, authentik creates a private credentials cache file for each source of type SPNEGO. If you'd like to customize that path or use your own credentials cache to avoid giving out a keytab to authentik, you can do so by setting this option to `TYPE:residual` of where the credentials cache is located. The format is the same as MIT Krb5, for instance: `FILE:/path/to/ccache`.
