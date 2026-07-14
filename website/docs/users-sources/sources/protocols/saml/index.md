---
title: SAML source
---

This source allows authentik to act as a SAML service provider. Like the [SAML provider](../../../../add-secure-apps/providers/saml/index.md), it supports signed requests. Vendor-specific documentation is available in the integrations section.

## Terminology

| Abbreviation | Name                       | Description                                                                                                                                  |
| ------------ | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| IdP          | Identity provider          | The authoritative SAML authentication source that holds the user database.                                                                   |
| SP           | Service provider           | The client that is connected to an IdP, usually providing a service, such as a web application. In the current context, authentik is the SP. |
| -            | Assertion                  | A message sent by the IdP asserting that the user has been identified.                                                                       |
| ACS          | Assertion Consumer Service | The service on the SP side that consumes the assertion sent from the IdP.                                                                    |
| SSO URL      | Single sign-on URL         | The URL on the IdP side that the SP calls to initiate an authentication process.                                                             |
| SLO URL      | Single logout URL          | The URL on the IdP side that the SP calls to invalidate a session and log the user out of the IdP and the SP.                                |

## Example configuration

If you have the provider metadata, you can extract the values that you need from it. The following table provides example values for a basic IdP metadata file.

| Name                       | Example                                                         | Description                                                                                                                                                                                                                                                                    |
| -------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Name                       | Company SAML                                                    | The name of the authentication source                                                                                                                                                                                                                                          |
| Slug                       | company-saml                                                    | The slug used in URLs for the source                                                                                                                                                                                                                                           |
| Icon                       | `branding/company-icon.svg`                                     | Optional icon or image shown for the source. See [File picker values](../../../../customize/file-picker.md).                                                                                                                                                                   |
| SSO URL                    | https://saml.company/login/saml                                 | The SingleSignOnService URL for the IdP. This value can be found in the metadata or IdP documentation. There can be different URLs for different binding types, such as HTTP-Redirect and HTTP-POST. Use the URL for the binding type that you choose below.                   |
| SLO URL                    | https://saml.company/logout/saml                                | The URL that is called when a user logs out of authentik. This can be used to automatically log the user out of the SAML IdP after logging out of authentik. Not all IdPs support or require this behavior.                                                                     |
| Binding Type               | HTTP-POST                                                       | How authentik communicates with the SSO URL (302 redirect or POST request). This will depend on what the provider supports.                                                                                                                                                    |
| Allow IdP-initiated logins | False                                                           | Whether to allow the IdP to log users into authentik without any interaction. Activating this can be a security risk because this request is not verified, and could be used by an attacker to authenticate a user without interaction.                                        |
| Force authentication       | False                                                           | When enabled, authentik requests the IdP to force re-authentication of the user, even if they already have an active session with the IdP.                                                                                                                                     |
| Issuer override            | `https://authentik.company/source/saml/<source-slug>/metadata/` | The identifier (Entity ID) for the authentik instance in the SAML federation. This is optional and defaults to the metadata URL of the source, as shown in the example. To override it, set any value that the IdP recognizes. This must match what you register on the IdP side. |
| NameID Policy              | Persistent                                                      | Depending on what the IdP sends as persistent ID, some IdPs use the username or email address while others use a random string or hashed value. If the user in authentik receives a random string as a username, try using **Email address** or **Windows**.                    |
| Flow settings              | Default                                                         | If there are custom flows in your instance for external authentication, select them here.                                                                                                                                                                                      |

## Add authentik as a service provider with your IdP

This depends on the software that you use for your IdP. On the **Metadata** tab in the SAML federation source, you can download the metadata for the service provider. This should let you import the service provider into most IdPs. If this does not work, the important parts are:

- Entity ID: Taken from the Issuer override field above
- Return URL/ACS URL: `https://authentik.company/source/saml/<source-slug>/acs/`
- Certificate: If you have chosen to sign your outgoing requests, use the public side of the certificate that you specified in the settings.

## Example IdP metadata

```xml
<md:EntityDescriptor entityID="https://saml.company/idp">
    <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol" WantAuthnRequestsSigned="false">
        <md:NameIDFormat>
            urn:oasis:names:tc:SAML:2.0:nameid-format:persistent
        </md:NameIDFormat>
        <md:NameIDFormat>
            urn:oasis:names:tc:SAML:2.0:nameid-format:transient
        </md:NameIDFormat>
        <md:NameIDFormat>
            urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress
        </md:NameIDFormat>
        <md:NameIDFormat>
            urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified
        </md:NameIDFormat>
        <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="https://saml.company/login/saml/"/>
        <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="https://saml.company/login/saml/"/>
    </md:IDPSSODescriptor>
    <md:Organization>
        <md:OrganizationName xml:lang="en">Example Organization</md:OrganizationName>
        <md:OrganizationDisplayName xml:lang="en">Example Organization</md:OrganizationDisplayName>
        <md:OrganizationURL xml:lang="en">http://www.company</md:OrganizationURL>
    </md:Organization>
    <md:ContactPerson contactType="technical">
        <md:Company>Example Organization</md:Company>
        <md:GivenName>John</md:GivenName>
        <md:SurName>Doe</md:SurName>
        <md:EmailAddress>john.doe@company</md:EmailAddress>
        <md:TelephoneNumber>012 345 67890</md:TelephoneNumber>
    </md:ContactPerson>
    <md:ContactPerson contactType="support">
        <md:Company>Example Organization</md:Company>
        <md:GivenName>Helpdesk</md:GivenName>
        <md:SurName>Support</md:SurName>
        <md:EmailAddress>helpdesk@company</md:EmailAddress>
        <md:TelephoneNumber>012 345 67890</md:TelephoneNumber>
    </md:ContactPerson>
</md:EntityDescriptor>
```

## SAML source property mappings

See the [overview](../../property-mappings/index.md) for information on how property mappings work.

SAML source property mappings customize the user and group properties created from a SAML assertion. authentik parses the assertion's `AttributeStatement` into the `properties` dictionary before custom mappings run, using each SAML attribute's `Name` as the dictionary key. Custom mappings can then translate those SAML attribute names to authentik user fields such as `username`, `email`, `name`, and `attributes`.

Property mappings do not change the internal SAML source connection identifier, which is based on the assertion's NameID. To persist mapped user fields, ensure the source flow that runs for the user includes a [User Write stage](../../../../add-secure-apps/flows-stages/stages/user_write/index.md) before the user login stage. For existing users, this is the source's authentication flow; for new users, this is the source's enrollment flow.

### Expression data

The following variables are available to SAML source property mappings:

The parsed XML objects use Python's standard [`xml.etree.ElementTree`](https://docs.python.org/3/library/xml.etree.elementtree.html) API.

- `root`: The parsed XML root containing data from the source.
- `assertion`: The parsed XML element containing the SAML assertion.
- `name_id`: The parsed XML element identifying the user.
- `properties`: A Python dictionary containing the source's parsed SAML attributes and the results of any previously run mappings.

### Example

This example maps common SAML attributes to authentik user fields. Replace the attribute names with the SAML attribute `Name` values sent by the external identity provider connected to this SAML source.

```python
email = properties.get("email") or properties.get("urn:oid:0.9.2342.19200300.100.1.3")
first_name = properties.get("firstname") or properties.get("urn:oid:2.5.4.42")
last_name = properties.get("lastname") or properties.get("urn:oid:2.5.4.4")

return {
    "username": email,
    "email": email,
    "name": f"{first_name or ''} {last_name or ''}".strip(),
    "attributes": {
        "first_name": first_name,
        "last_name": last_name,
    },
}
```

If you need to read the XML assertion directly, use the SAML assertion namespace when searching for elements:

```python
NS_SAML_ASSERTION = "urn:oasis:names:tc:SAML:2.0:assertion"

attributes = {}
for attribute in assertion.findall(f".//{{{NS_SAML_ASSERTION}}}Attribute"):
    values = [
        value.text
        for value in attribute.findall(f"{{{NS_SAML_ASSERTION}}}AttributeValue")
    ]
    attributes[attribute.attrib["Name"]] = values[0] if len(values) == 1 else values

return {
    "email": attributes.get("email"),
}
```
