---
title: SAML Provider
---

The SAML provider allows you to integrate with services and applications using the SAML2 protocol. It supports signed requests and uses [property mappings](../property-mappings/index.md#saml-property-mappings) to determine which fields are exposed and what values they return. This makes it possible to expose application-specific fields. Default fields are exposed through auto-generated property mappings, which are prefixed with "authentik default".

Refer to the instructions to [create a SAML provider](./create-saml-provider.md).

## SAML bindings and endpoints

Bindings are the mechanism that handle how SAML messages are exchanged between between an Identity Provider (IdP) and a Service Provider (SP), typically a service or application. Both IdPs and SPs define various endpoints in their metadata, each associated with a specific SAML binding.

A binding defines how these SAML messages are transported over network protocols; the endpoint URL specifies where and how the messages are sent according to that binding.

In authentik, you can define two SAML bindings: `HTTP Redirect` or `HTTP POST`. The table below shows the supported endpoints for each binding.

| Endpoint                  | URL                                                          |
| ------------------------- | ------------------------------------------------------------ |
| SSO (Redirect binding)    | `/application/saml/<application_slug>/sso/binding/redirect/` |
| SSO (POST binding)        | `/application/saml/<application_slug>/sso/binding/post/`     |
| SSO (IdP-initiated login) | `/application/saml/<application_slug>/sso/binding/init/`     |
| SLO (Redirect binding)    | `/application/saml/<application_slug>/slo/binding/redirect/` |
| SLO (POST binding)        | `/application/saml/<application_slug>/slo/binding/post/`     |
| Metadata Download         | `/application/saml/<application_slug>/metadata/`             |

## SAML metadata

Describe the basics of metadata. But put any procedurals over in the How To doc (and link to from here).

BASICS: After you create your app (SP) and your SAML provider, you go back on the provider page and you can download the SP metadata.

- BUT… do our users need our IdP-generated metadata file? And if so where do they get it from? How do we create it for them?

## Signing and certificates

TODO write words here about the Signing Certificate and the other type of certs (see UI for Creating a new App (with SAML provider) under Advanced Protocols...)

## Property mappings in SAML

Attributes defined within a property mapping are used to provide information about a user to a service provider when a SAML-based single sign-on (SSO) process is started, such as name, username, email address, group membership, or even a custom attribute.

Attribute name used for SAML Assertions. Can be a URN OID, a schema reference, or any other string.

During the sign on and authentication process, communication between the SP (say the application that the user is attempting to log in to) and the IdP (the identity provider software managing the SSO work) replies on property mappings to align, or "map" the attributes' values between the SP and IdP.

... talk here about the first name and last name thing (just use `Name`)...

### Default SAML property mappings

The following property mappings are automatically added when you create a new SAML provider and can be removed at will.

| Property Mapping Name                                         | SAML Attribute Name                                                          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| authentik default SAML Mapping: Email                         | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`         |
| authentik default SAML Mapping: Groups                        | `http://schemas.xmlsoap.org/claims/Group`                                    |
| authentik default SAML Mapping: Name                          | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`                 |
| authentik default SAML Mapping: UPN                           | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn`                  |
| authentik default SAML Mapping: User ID                       | `http://schemas.goauthentik.io/2021/02/saml/uid`                             |
| authentik default SAML Mapping: Username                      | `http://schemas.goauthentik.io/2021/02/saml/username`                        |
| authentik default SAML Mapping: WindowsAccountName (Username) | `http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname` |

They can be viewed on the **Property Mappings** page of the admin interface by disabling the **Hide managed mappings** toggle.

### Custom property mappings

If there is not already a property mapping that works for what you need, you can [create a custom property mapping](../property-mappings/) or edit one of the existing mappings.

Some useful custom SAML property mappings include:

:::note
The `authentik default SAML Mapping: Name` property mapping returns first name (givenname) and last name (surname) in one string. Some SPs require these attributes to be separate.
:::

#### `surname`

- SAML Attribute Name: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname`

- Expression:

    ```python
    return request.user.name.rsplit(" ", 1)[-1]
    ```

#### `givenname`

- SAML Attribute Name: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname`

- Expression:

    ```python
    return request.user.name.split(" ", 1)[0]
    ```

### `Name ID`

The Name_ID element is an important type of attribute, a unique identifier for that user. While the other attributes might change (givenname, email address, etc) the Name_ID is persistent and should never change.

When the IdP sends a SAML assertion to the SP, the NameID is the unique identifier used to represent a specific user in the assertion. It's not used for authentication itself, only for identification purposes in the assertion.

The SP also tells the IdP what format the IdP should use when creating the assertion. Under certain circumstances, the SP cannot tell us what format they want, like if the user is already in authentik and click the app to log in to it… but by making it a property mapping we do not get stopped on this snag. We default to the unspecified format, but of course the value is already set in the property mapping, so authn carries on.

You can select a custom SAML property mapping from which the NameID field will be generated. If left default, the following checks are done:

- When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`, the NameID will be set to the hashed user ID.
- When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:X509SubjectName`, the NameID will be set to the user's `distinguishedName` attribute. This attribute is set by the LDAP source by default. If the attribute does not exist, it will fall back the persistent identifier.
- When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:WindowsDomainQualifiedName`, the NameID will be set to the user's UPN. This is also set by the LDAP source, and also falls back to the persistent identifier.
- When the request asks for `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`, the NameID will be set based on the user's session ID.
- When the request asks for `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`, the NameID will be set to the user's email address.

:::warning
Keep in mind that with the default settings, users are free to change their email addresses. - Therefore, it is recommended to either: - disallow users to change their email addresses - use `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent` as the Name ID format in the SP (if possible), because this this cannot be changed.
:::

### `AuthnContextClassRef` property mapping

Another special type of attribute is `AuthnContextClassRef`, used in SAML authentication requests from SPs to specify the required or preferred authentication contexts from the IdP. The authentication context specifies the desired or required level of authentication for a user. For example, Microsoft Entra ID uses the `AuthnContextClassRef` element to enforce specific authentication requirements for any applications accessing Entra ID.

In authentik, you can use a property mapping to configure how the `AuthnContextClassRef` value is created. When left empty, the AuthnContextClassRef will be set based on the authentication method that the user used to authenticate.

... ensure that the AuthnContextClassRef element in the SAML message is a URI.
