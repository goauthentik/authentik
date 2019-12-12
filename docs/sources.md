# Sources

Sources allow you to connect passbook to an existing User directory. They can also be used for Social-Login, using external Providers like Facebook, Twitter, etc.

## Generic OAuth Source

**All Integration-specific Sources are documented in the Integrations Section**

This source allows users to enroll themselves with an External OAuth-based Identity Provider. The Generic Provider expects the Endpoint to return OpenID-Connect compatible Information. Vendor specific Implementations have their own OAuth Source.

-   Policies: Allow/Forbid Users from linking their Accounts with this Provider
-   Request Token URL: This field is used for OAuth v1 Implementations and will be provided by the Provider.
-   Authorization URL: This value will be provided by the Provider.
-   Access Token URL: This value will be provided by the Provider.
-   Profile URL: This URL is called by passbook to retrieve User information upon successful authentication.
-   Consumer key/Consumer secret: These values will be provided by the Provider.

## SAML Source

This source allows passbook to act as a SAML Service Provider. Just like the SAML Provider, it supports signed Requests. Vendor specific documentation can be found in the Integrations Section

## LDAP Source

This source allows you to import Users and Groups from an LDAP Server

-   Server URI: URI to your LDAP Server/Domain Controller
-   Bind CN: CN to bind as, this can also be a UPN in the format of `user@domain.tld`
-   Bind password: Password used during the bind process
-   Enable Start TLS: Enables StartTLS functionality. To use SSL instead, use port `636`
-   Base DN: Base DN used for all LDAP queries
-   Addition User DN: Prepended to Base DN for User-queries.
-   Addition Group DN: Prepended to Base DN for Group-queries.
-   User object filter: Consider Objects matching this filter to be Users.
-   Group object filter: Consider Objects matching this filter to be Groups.
-   User group membership field: Field which contains Groups of user.
-   Object uniqueness field: Field which contains a unique Identifier.
-   Sync groups: Enable/disable Group synchronization. Groups are synced in the background every 5 minutes.
-   Sync parent group: Optionally set this Group as parent Group for all synced Groups (allows you to, for example, import AD Groups under a root `imported-from-ad` group.)
-   Property mappings: Define which LDAP Properties map to which passbook Properties. The default set of Property Mappings is generated for Active Directory. See also [LDAP Property Mappings](property-mappings.md#ldap-property-mapping)
