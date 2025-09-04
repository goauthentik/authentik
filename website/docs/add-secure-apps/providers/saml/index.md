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

SAML Metadata ensures that SAML single sign-on works reliably by exchanging and maintaining identity and connection information. SAML metadata is an XML document that defines how IdPs and SPs securely interact for authentication. It includes information such as endpoints, bindings, certificates, and unique identifiers.

SAML metadata can be imported into authentik(put a link here to procedure) to automatically configure a SAML provider based on the requirements of an SP.

SAML metadata can also be exported from an authentik SAML provider(put a link to procedure) to an SP to automatically provide important endpoint and certificate information to an SP.

## Signing and certificates

Certificates are vital for trust and security during SAML authentication.

### Signing certificates

A signing certificate allow authentik to digitally sign SAML assertions and responses. This certificate contains a private key that creates a cryptographic signature, proving the authenticity and integrity of the transmitted data. The SP then uses the corresponding public key from this certificate to verify the signature. Ensuring the response was not tampered with and that it originated from authentik.

Signing algorithms (such as ECDSA-SHA256) define the cryptographic method used for creating and validating the signatures.

### Verification certificates

A verification certificate in authentik acts as the public key used to verify digital signatures on SAML responses and assertions from an SP. When a SAML message is received, authentik validates it by comparing the signature against its configured verification certificate, ensuring that messages are authentic and originated from the SP.

### Encryption certificates

An encryption certificate is a public key certificate used by authentik to encrypt sensitive data in SAML assertions before sending them to an SP. This ensures that sensitive data within the assertion, such as user attributes and authentication details, remain confidential and can only be decrypted by the SP possessing the corresponding private key.

## Property mappings in SAML

During a SAML authentication process, communication between the SP and the IdP replies on property mappings to align, or "map" user attributes values between the IdP and SP.

Each SAML property mapping includes the following fields:

    - **Name**: The name of the property mapping that's displayed in the authentik admin interface.
    - **SAML Attribute Name**: The label that maps IdP user information to SP expectations. Can be a URN OID, a schema reference, or any other string.
    - **Friendly Name**: A human-friendly identifier for a SAML attribute.
    - **Expression**: The python expression that maps an authentik user attribute to a value that an SP is expecting.

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

The default SAML property mappings can be viewed on the **Property Mappings** page of the admin interface by disabling the **Hide managed mappings** toggle.

### Custom property mappings

If there is not already a property mapping that maps the user attributes that your SP requires, you can [create a custom property mapping](../property-mappings/) or edit one of the existing mappings.

For example, some SPs require users' first name (givenname) and last name (surname) attributes to be provided separately. However, the `authentik default SAML Mapping: Name` property mapping returns both attributes as one string. The following custom property mappings can be useful in such cases:

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

### `NameID`

The `NameID` attribute acts as a unique identifier for an user. While other attributes might change (givenname, email address, etc) the `NameID` attribute is persistent and should never change. When the IdP sends a SAML assertion to the SP, the `NameID` is the unique identifier used to represent a specific user in the assertion. It's not used for authentication itself, only for identification purposes in the assertion.

In authentik, it's possible to set the `NameID` attribute to any property mapping that's enabled on a SAML provider. This is done via the **NameID property mapping** field on a SAML provider.

Alternatively, when the **NameID property mapping** field is left unpopulated on a SAML provider, the `NameID` attribute will be set based on the SP's request as follows:

| SAML attribute request by SP                                           | How authentik will handle the NameId                                                                                                                                                                 |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`                 | `NameID` will be set to the hashed user ID.                                                                                                                                                          |
| `urn:oasis:names:tc:SAML:2.0:nameid-format:X509SubjectName`            | `NameID` will be set to the user's `distinguishedName` attribute. This attribute is set by the LDAP source by default. If the attribute does not exist, it will fall back the persistent identifier. |
| `urn:oasis:names:tc:SAML:2.0:nameid-format:WindowsDomainQualifiedName` | `NameID` will be set to the user's UPN. This is also set by the LDAP source, and also falls back to the persistent identifier.                                                                       |
| `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`                  | `NameID` will be set based on the user's session ID.                                                                                                                                                 |
| `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`               | `NameID` will be set to the user's email address.                                                                                                                                                    |

:::warning
By default, users are free to change their email addresses. Therefore, it is recommended to either: disallow changing email addresses or, if possible, use `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent` as the `NameID` format in the SP.
:::

### `AuthnContextClassRef`

The `AuthnContextClassRef` attribute appears in the SAML assertion and contains a URI that describes the assurance level, such as password, multi-factor, or smartcard authentication. SPs use this information to understand and verify how the user was authenticated by an IdP.

In authentik, it's possible to set the `AuthnContextClassRef` attribute to any property mapping that's enabled on a SAML provider. This is done via the **AuthnContextClassRef Property Mapping** on a SAML provider.

Alternatively, when the **AuthnContextClassRef Property Mapping** field is left unpopulated on a SAML provider, the `AuthnContextClassRef` will be set based on the authentication method that the user used to authenticate.
