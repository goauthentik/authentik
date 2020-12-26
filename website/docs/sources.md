---
title: Sources
---

Sources allow you to connect authentik to an existing user directory. They can also be used for social logins, using external providers such as Facebook, Twitter, etc.

## Generic OAuth Source

**All Integration-specific Sources are documented in the Integrations Section**

This source allows users to enroll themselves with an external OAuth-based Identity Provider. The generic provider expects the endpoint to return OpenID-Connect compatible information. Vendor-specific implementations have their own OAuth Source.

-   Policies: Allow/Forbid users from linking their accounts with this provider.
-   Request Token URL: This field is used for OAuth v1 implementations and will be provided by the provider.
-   Authorization URL: This value will be provided by the provider.
-   Access Token URL: This value will be provided by the provider.
-   Profile URL: This URL is called by authentik to retrieve user information upon successful authentication.
-   Consumer key/Consumer secret: These values will be provided by the provider.

## SAML Source

This source allows authentik to act as a SAML Service Provider. Just like the SAML Provider, it supports signed requests. Vendor-specific documentation can be found in the Integrations Section.

## LDAP Source

This source allows you to import users and groups from an LDAP Server.

:::info
For Active Directory, follow the [Active Directory Integration](https://goauthentik.io/docs/integrations/sources/active-directory/index)
:::

-   Server URI: URI to your LDAP server/Domain Controller.
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
-   Property mappings: Define which LDAP properties map to which authentik properties. The default set of property mappings is generated for Active Directory. See also [LDAP Property Mappings](property-mappings/index.md#ldap-property-mapping)
