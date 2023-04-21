---
title: SAML Provider
---

This provider allows you to integrate enterprise software using the SAML2 Protocol. It supports signed requests and uses [Property Mappings](../../property-mappings/#saml-property-mapping) to determine which fields are exposed and what values they return. This makes it possible to expose vendor-specific fields.
Default fields are exposed through auto-generated Property Mappings, which are prefixed with "authentik default".

| Endpoint                  | URL                                                          |
| ------------------------- | ------------------------------------------------------------ |
| SSO (Redirect binding)    | `/application/saml/<application slug>/sso/binding/redirect/` |
| SSO (POST binding)        | `/application/saml/<application slug>/sso/binding/post/`     |
| SSO (IdP-initiated login) | `/application/saml/<application slug>/sso/binding/init/`     |
| SLO (Redirect binding)    | `/application/saml/<application slug>/slo/binding/redirect/` |
| SLO (POST binding)        | `/application/saml/<application slug>/slo/binding/post/`     |
| Metadata Download         | `/application/saml/<application slug>/metadata/`             |

You can download the metadata through the Webinterface, this link might be handy if your software wants to download the metadata directly.

The metadata download link can also be copied with a button on the provider overview page.

## Name ID

You can select a custom SAML Property Mapping after which the NameID field will be generated. If left default, the following checks are done:

-   When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`, the NameID will be set to the hashed user ID.
-   When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:X509SubjectName`, the NameID will be set to the user's `distinguishedName` attribute. This attribute is set by the LDAP source by default. If the attribute does not exist, it will fall back the persistent identifier.
-   When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:WindowsDomainQualifiedName`, the NameID will be set to the user's UPN. This is also set by the LDAP source, and also falls back to the persistent identifier.
-   When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`, the NameID will be set based on the user's session ID.
-   When the request asks for `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`, the NameID will be set to the user's email address.

    :::warning
    Keep in mind that with the default settings, users are free to change their email addresses. As such it is recommended to use `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`, as this cannot be changed.
    :::
