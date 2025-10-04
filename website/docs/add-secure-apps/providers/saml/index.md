---
title: SAML Provider
---

The SAML provider allows you to integrate with Service Providers using the SAML2 protocol. It supports [importing and exporting SAML metadata](#saml-metadata), [signed requests](#certificates) and uses [property mappings](../property-mappings/index.md#saml-property-mappings) to align, or "map", Service Provider and authentik attributes.

Refer to our documentation to learn how to [create a SAML provider](./create-saml-provider.md).

## SAML bindings and endpoints

Bindings define how SAML messages are exchanged between an Identity Provider (IdP) and a Service Provider (SP), typically a service or application. Both IdPs and SPs define various endpoints in their metadata, each associated with a specific SAML binding.

A binding defines how SAML messages are transported over network protocols. In authentik, you can select one of two SAML bindings: `HTTP Redirect` or `HTTP POST`.

Endpoint URLs specify where and how the messages are sent according to that binding. The table below shows the supported endpoints for each binding:

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

### Importing SP SAML metadata

You can [import SP SAML metadata](./create-saml-provider.md#create-a-saml-provider-from-sp-metadata-import-sp-metadata) to automatically configure a SAML provider based on the requirements of an SP.

### Exporting authentik SAML metadata

You can [export SAML metadata from an authentik SAML provider](./create-saml-provider.md#export-authentik-saml-provider-metadata) to an SP to automatically provide important endpoint and certificate information to the SP.

## Certificates

Certificates are vital for trust and security during SAML authentication and are used for several purposes.

### Signing certificates

A signing certificate allows authentik to digitally sign SAML assertions and responses. This certificate contains a private key that creates a cryptographic signature, proving the authenticity and integrity of the transmitted data. The SP then uses the corresponding public key from this certificate to verify the signature. Ensuring the response was not tampered with and that it originated from authentik.

#### Signing algorithm

Signing algorithms (such as RSA-SHA256 or ECDSA-SHA256) define the cryptographic method used for creating and validating the signatures.

#### Digest algorithm

A digest algorithm is a cryptographic hash function used to create a fixed-size hash (digest) from the data in the SAML assertion or message. authentik computes a digest value using the chosen algorithm (such as SHA-1 or SHA-256), and it is included as part of the digital signature process. The SP uses the same digest algorithm to independently compare it with the received digest to validate the integrity of the received assertion or message.

### Verification certificates

A verification certificate in authentik acts as the public key used to verify digital signatures on SAML responses and assertions from an SP. When a SAML message is received, authentik validates it by comparing the signature against its configured verification certificate, ensuring that messages originated from the SP.

### Encryption certificates

An encryption certificate is a public key certificate used by authentik to encrypt sensitive data in SAML assertions before sending them to an SP. This ensures that sensitive data within the assertion, such as user attributes and authentication details, remain confidential and can only be decrypted by the SP possessing the corresponding private key.

## SAML property mappings

During a SAML authentication process, communication between the SP and the IdP relies on property mappings to align, or "map", user attributes values between the IdP and SP.

Each SAML property mapping includes the following fields:

    - **Name**: The name of the property mapping that's displayed in the authentik admin interface.
    - **SAML Attribute Name**: The label that maps IdP user information to SP expectations. Can be a URN OID, a schema reference, or any other string.
    - **Friendly Name**: A human-friendly identifier for a SAML attribute.
    - **Expression**: The Python expression that maps an authentik user attribute to a value that an SP is expecting.

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

### Custom SAML property mappings

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

## NameID

The NameID attribute acts as a unique identifier for a user. While other attributes might change (givenname, email address, etc) the NameID attribute is persistent and should never change. When the IdP sends a SAML assertion to the SP, the NameID is the unique identifier used to represent a specific user in the assertion. It's not used for authentication itself, only for identification purposes in the assertion.

### NameID property mapping

In authentik, it's possible to configure which property mapping will be used to create the NameID value. The **NameID property mapping** field on a SAML provider can be set to any property mapping that's enabled on a SAML provider. When left empty, the NameID Policy of the incoming SP request will be respected.

### Default NameID policy

In authentik, it's also possible to configure the default SAML NameID policy used for IDP-initiated logins or when an incoming SP assertion doesn't specify a NameID policy (also applies when using a custom NameID Mapping). The following table outlines how NameID policies are handled:

| Default NameID policy                                                            | How authentik will handle the NameID                                                                                                                                                               |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Persistent - `urn:oasis:names:tc:SAML:2.0:nameid-format:persistent`              | NameID will be set to the user's hashed ID.                                                                                                                                                        |
| x509 Subject - `urn:oasis:names:tc:SAML:2.0:nameid-format:X509SubjectName`       | NameID will be set to the user's `distinguishedName` attribute. This attribute is set by the LDAP source by default. If the attribute does not exist, it will fall back the persistent identifier. |
| Windows - `urn:oasis:names:tc:SAML:2.0:nameid-format:WindowsDomainQualifiedName` | NameID will be set to the user's UPN. This is also set by the LDAP source, and also falls back to the persistent identifier.                                                                       |
| Transient - `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`                | NameID will be set based on the user's session ID.                                                                                                                                                 |
| Email address - `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`         | NameID will be set to the user's email address.                                                                                                                                                    |

:::warning
By default, users are free to change their email addresses. Therefore, it is recommended to either: disallow changing email addresses or, if possible, avoid using a user's email address as the NameID attribute.
:::

## AuthnContextClassRef

The AuthnContextClassRef attribute appears in the SAML assertion and contains a URI that describes the assurance level, such as password, multi-factor, or smartcard authentication. SPs use this information to understand and verify how the user was authenticated by an IdP.

In authentik, it's possible to set the AuthnContextClassRef attribute to any property mapping that's enabled on a SAML provider. This is done via the **AuthnContextClassRef Property Mapping** on a SAML provider.

Alternatively, when the **AuthnContextClassRef Property Mapping** field is left unpopulated on a SAML provider, the AuthnContextClassRef will be set based on the method that the user authenticated with.
