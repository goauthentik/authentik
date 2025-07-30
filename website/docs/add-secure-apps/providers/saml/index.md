---
title: SAML Provider
---

This provider allows you to integrate enterprise software using the SAML2 protocol. It supports signed requests and uses [property mappings](../property-mappings/index.md#saml-property-mappings) to determine which fields are exposed and what values they return. This makes it possible to expose vendor-specific fields.
Default fields are exposed through auto-generated Property Mappings, which are prefixed with "authentik default".

## authentik and SAML

words here.......

## SAML Bindings

Bindings are the mechanism that handle how SAML messages are exchanged between between an Identity Provider (IdP) and a Service Provider (SP). Both IdPs and SPs define various endpoints in their metadata, each associated with a specific SAML binding.

A binding defines how these SAML messages are transported over network protocols; the endpoint URL specifies where and how the messages are sent according to that binding.

In authentik, you can define two communication protocols: `HTTP Redirect` or `HTTP POST`. The table below shows the supported endpoints you can use when creating bindings for SAML.

| Endpoint                  | URL                                                          |
| ------------------------- | ------------------------------------------------------------ |
| SSO (Redirect binding)    | `/application/saml/<application slug>/sso/binding/redirect/` |
| SSO (POST binding)        | `/application/saml/<application slug>/sso/binding/post/`     |
| SSO (IdP-initiated login) | `/application/saml/<application slug>/sso/binding/init/`     |
| SLO (Redirect binding)    | `/application/saml/<application slug>/slo/binding/redirect/` |
| SLO (POST binding)        | `/application/saml/<application slug>/slo/binding/post/`     |
| Metadata Download         | `/application/saml/<application slug>/metadata/`             |

You can download the metadata through the Web interface; this link might be handy if your software wants to download the metadata directly.

The metadata download link can also be copied with a button on the provider overview page.

## Attributes for SAML provider

Words in here about what attributes are and how used...."attributes are used to convey information about a user to a service provider during a SAML-based single sign-on (SSO) process"...

Talk about how the attributes are what are used in property mappings... how custom attributes can be created and mapped .... List our default attributes... talk about the fist name and last name thing (just use `Name`)...

### Default property mappings

The following attributes are available as property mappings through the Admin interface when you are creating a new SAML provider.

###

### Custom property mappings

Some useful custom property mappings include:

#### `surname`

- SAML Attribute Name: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname

- Expression: `return request.user.name.rsplit(" ", 1)[-1]`

#### `givenname`

- SAML Attribute Name: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname

- Expression: `return request.user.name.split(" ", 1)[0]`

#### Name ID

The Name_ID element is another, special, type of attribute, a unique identifier for that user. o while the other attributes might change (givenname, email address, etc) the Name_ID needs to never change.

You can select a custom SAML property mapping after which the NameID field will be generated. If left default, the following checks are done:

- When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`, the NameID will be set to the hashed user ID.
- When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:X509SubjectName`, the NameID will be set to the user's `distinguishedName` attribute. This attribute is set by the LDAP source by default. If the attribute does not exist, it will fall back the persistent identifier.
- When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:WindowsDomainQualifiedName`, the NameID will be set to the user's UPN. This is also set by the LDAP source, and also falls back to the persistent identifier.
- When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`, the NameID will be set based on the user's session ID.
- When the request asks for `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`, the NameID will be set to the user's email address.

#### Custom property mappings

Some useful custom property mappings include:

#### `surname`

- SAML Attribute Name: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname

- Expression: `return request.user.name.rsplit(" ", 1)[-1]`

#### `givenname`

- SAML Attribute Name: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname

- Expression: `return request.user.name.split(" ", 1)[0]`

:::warning
Keep in mind that with the default settings, users are free to change their email addresses. As such it is recommended to use `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`, as this cannot be changed.
:::
