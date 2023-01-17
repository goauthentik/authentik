---
title: LDAP
---

Sources allow you to connect authentik to an existing user directory. They can also be used for social logins, using external providers such as Facebook, Twitter, etc.

## LDAP Source

This source allows you to import users and groups from an LDAP Server.

:::info
For Active Directory, follow the [Active Directory Integration](../active-directory/)

For FreeIPA, follow the [FreeIPA Integration](../freeipa/)
:::

-   Server URI: URI to your LDAP server/Domain Controller.

    You can specify multiple servers by separating URIs with a comma, like `ldap://ldap1.company,ldap://ldap2.company`.

    When using a DNS entry with multiple Records, authentik will select a random entry when first connecting.

-   Bind CN: CN of the bind user. This can also be a UPN in the format of `user@domain.tld`.
-   Bind password: Password used during the bind process.
-   Enable StartTLS: Enables StartTLS functionality. To use LDAPS instead, use port `636`.
-   Base DN: Base DN used for all LDAP queries.
-   Addition User DN: Prepended to the base DN for user queries.
-   Addition Group DN: Prepended to the base DN for group queries.
-   User object filter: Consider objects matching this filter to be users.
-   Group object filter: Consider objects matching this filter to be groups.
-   User group membership field: This field contains the user's group memberships.
-   Object uniqueness field: This field contains a unique identifier.
-   Sync groups: Enable/disable group synchronization. Groups are synced in the background every 5 minutes.
-   Sync parent group: Optionally set this group as the parent group for all synced groups. An example use case of this would be to import Active Directory groups under a root `imported-from-ad` group.
-   Property mappings: Define which LDAP properties map to which authentik properties. The default set of property mappings is generated for Active Directory. See also [LDAP Property Mappings](../../../docs/property-mappings/#ldap-property-mapping)

## Property mappings

LDAP property mappings can be used to convert the raw LDAP response into an authentik user/group.

By default, authentik ships with some pre-configured mappings for the most common LDAP setups.

You can assign the value of a mapping to any user attribute, or save it as a custom attribute by prefixing the object field with `attribute.` Keep in mind though, data types from the LDAP server will be carried over. This means that with some implementations, where fields are stored as array in LDAP, they will be saved as array in authentik. To prevent this, use the built-in `list_flatten` function.

## Troubleshooting

To troubleshoot LDAP sources and their synchronization, see [LDAP Troubleshooting](../../../docs/troubleshooting/ldap_source)
