---
title: LDAP Source
---

Sources allow you to connect authentik to an existing user directory. This source allows you to import users and groups from an LDAP Server.

:::info
For Active Directory, follow the [Active Directory Integration](../../directory-sync/active-directory/index.md)

For FreeIPA, follow the [FreeIPA Integration](../../directory-sync/freeipa/index.md)
:::

## Configuration options for LDAP sources

To create or edit a source in authentik, open the Admin interface and navigate to **Directory -> Ferderation and Social login**. There you can create a new LDAP source, or edit an existing one, using the following settings.

- **Enabled**: Toggle this option on to allow authentik to use the defined LDAP source.

- **Update internal password on login**: When the user logs in to authentik using the LDAP password backend, the password is stored as a hashed value in authentik. Toggle off (default setting) if you do not want to store the hashed passwords in authentik.

- **Sync users**: Enable or disable user synchronization between authentik and the LDAP source.

- **User password writeback**: Enable this option if you want to write password changes that are made in authentik back to LDAP.

- **Sync groups**: Enable/disable group synchronization. Groups are synced in the background every 5 minutes.

- **Parent group**: Optionally set this group as the parent group for all synced groups. An example use case of this would be to import Active Directory groups under a root `imported-from-ad` group.

#### Connection settings

- **Server URI**: URI to your LDAP server/Domain Controller. You can specify multiple servers by separating URIs with a comma, like `ldap://ldap1.company,ldap://ldap2.company`. When using a DNS entry with multiple Records, authentik will select a random entry when first connecting.

    - **Enable StartTLS**: Enables StartTLS functionality. To use LDAPS instead, use port `636`.
    - **Use Server URI for SNI verification**: this setting is required for servers using TLS 1.3+

- **TLS Verification Certificate**: Specify a keypair to validate the remote certificate.

- **TLS Client authentication**: Client certificate keypair to authenticate against the LDAP Server's Certificate.

- **Bind CN**: CN of the bind user. This can also be a UPN in the format of `user@domain.tld`.

- **Bind password**: Password used during the bind process.

- **Base DN**: Base DN (distinguished name) used for all LDAP queries.

#### LDAP Attribute mapping

- **User Property Mappings** and **Group Property Mappings**: Define which LDAP properties map to which authentik properties. The default set of property mappings is generated for Active Directory. See also our documentation on [property mappings](#ldap-source-property-mappings).

    :::warning
    When the **Sync users** and or the **Sync groups** options are enabled, their respective property mapping options must have at least one mapping selected, otherwise the sync will not start.
    :::

#### Additional Settings

- **Group**: Parent group for all the groups imported from LDAP.

- **User path**: Path template for all new users created.

- **Addition User DN**: Prepended to the base DN for user queries.

- **Addition Group DN**: Prepended to the base DN for group queries.

- **User object filter**: Consider objects matching this filter to be users.

- **Group object filter**: Consider objects matching this filter to be groups.

- **Group membership field**: This field contains the user's group memberships.

- **Object uniqueness field**: This field contains a unique identifier.

## LDAP source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work.

By default, authentik ships with [pre-configured mappings](#built-in-property-mappings) for the most common LDAP setups. These mappings can be found on the LDAP Source Configuration page in the Admin interface.

You can assign the value of a mapping to any user attribute. Keep in mind though, data types from the LDAP server will be carried over. This means that with some implementations, where fields are stored as array in LDAP, they will be saved as array in authentik. To prevent this, use the built-in `list_flatten` function. Here is an example mapping for the user's username and a custom attribute for a phone number:

```python
return {
    "username": ldap.get("uid"), # list_flatten is automatically applied to top-level attributes
    "attributes": {
        "phone": list_flatten(ldap.get("phoneNumber")), # but not for attributes!
    },
}
```

### Built-in property mappings

LDAP property mappings are used when you define a LDAP source. These mappings define which LDAP property maps to which authentik property. By default, the following mappings are created:

- authentik default Active Directory Mapping: givenName
- authentik default Active Directory Mapping: sAMAccountName
- authentik default Active Directory Mapping: sn
- authentik default Active Directory Mapping: userPrincipalName
- authentik default LDAP Mapping: mail
- authentik default LDAP Mapping: Name
- authentik default OpenLDAP Mapping: cn
- authentik default OpenLDAP Mapping: uid

These are configured with most common LDAP setups.

### Expression data

The following variables are available to LDAP source property mappings:

- `ldap`: A Python dictionary containing data from LDAP.
- `dn`: The object DN.

### Additional expression semantics

If you need to skip synchronization for a specific object, you can raise the `SkipObject` exception:

```python
if ldap.get("cn") == "doNotSync":
    raise SkipObject
```

## Password login

By default, authentik doesn't update the password it stores for a user when they log in using their LDAP credentials. That means that if the LDAP server is not reachable by authentik, users will not be able to log in. This behavior can be turned on with the **Update internal password on login** setting on the LDAP source.

:::note
Sources created prior to the 2024.2 release have this setting turned on by default.
:::

Be aware of the following security considerations when turning on this functionality:

- Updating the LDAP password does not invalidate the password stored in authentik; however for LDAP Servers like FreeIPA and Active Directory, authentik will lock its internal password during the next LDAP sync. For other LDAP servers, the old passwords will still be valid indefinitely.
- Logging in via LDAP credentials overwrites the password stored in authentik if users have different passwords in LDAP and authentik.
- Custom security measures that are used to secure the password in LDAP may differ from the ones used in authentik. Depending on threat model and security requirements this could lead to unknowingly being non-compliant.

## Troubleshooting

To troubleshoot LDAP sources and their synchronization, see [LDAP Troubleshooting](../../../../troubleshooting/ldap_source.md).
