---
title: SAML Source
---

This source allows authentik to act as a SAML Service Provider. Just like the [SAML provider](../../../../add-secure-apps/providers/saml/index.md), it supports signed requests. Vendor-specific documentation can be found in the Integrations section.

## Terminology

| Abbreviation | Name                       | Description                                                                                                                                 |
| ------------ | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| IDP          | Identity Provider          | The authoritative SAML authentication source that holds the user database                                                                   |
| SP           | Service Provider           | The client which is connected to an IDP, usually providing a service (e.g. a web application). In the current context, authentik is the SP. |
| -            | Assertion                  | A message sent by the IDP asserting that the user has been identified                                                                       |
| ACS          | Assertion Consumer Service | The service on the SP side that consumes the assertion sent from the IDP                                                                    |
| SSO URL      | Single Sign-On URL         | The URL on the IDP side which the SP calls to initiate an authentication process                                                            |
| SLO URL      | Single Log-Out URL         | The URL on the IDP side which the SP calls to invalidate a session and logout the user from the IDP as well as the SP                       |

## Example configuration

If you have the provider metadata, you should be able to extract all values you need from this. There is an example provided for a basic IDP metadata file below.

| Name                       | Example                          | Description                                                                                                                                                                                                                                                                    |
| -------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Name                       | Company SAML                     | The name of the authentication source                                                                                                                                                                                                                                          |
| Slug                       | company-saml                     | The slug used in URLs for the source                                                                                                                                                                                                                                           |
| Icon                       | `branding/company-icon.svg`      | Optional icon or image shown for the source. See [File picker values](../../../../customize/file-picker.md).                                                                                                                                                                   |
| SSO URL                    | https://saml.company/login/saml  | The SingleSignOnService URL for the IDP, this can be found in the metadata or IDP documentation. There can be different URLs for different Binding Types (e.g. HTTP-Redirect and HTTP-POST), use the URL corresponding to the binding type you choose below                    |
| SLO URL                    | https://saml.company/logout/saml | The URL that is called when a user logs out of authentik, can be used to automatically log the user out of the SAML IDP after logging out of authentik. Not supported by all IDPs, and not always wanted behaviour.                                                            |
| Issuer/Entity ID           | https://authentik.company        | The identifier for the authentik instance in the SAML federation, can be chosen freely. This is used to identify the SP on the IDP side, it usually makes sense to configure this to the URL of the SP or the path corresponding to the SP (e.g. `/source/saml/<source-slug>/` |
| Binding Type               | HTTP-POST                        | How authentik communicates with the SSO URL (302 redirect or POST request). This will depend on what the provider supports.                                                                                                                                                    |
| Allow IDP-Initiated Logins | False                            | Whether to allow the IDP to log users into authentik without any interaction. Activating this may constitute a security risk since this request is not verified, and could be utilized by an attacker to authenticate a user without interaction on their side.                |
| NameID Policy              | Persistent                       | Depending on what the IDP sends as persistent ID, some IDPs use the username or email address while others will use a random string/hashed value. If the user in authentik receives a random string as a username, try using Email address or Windows                          |
| Flow settings              | Default                          | If there are custom flows in your instance for external authentication, change to use them here                                                                                                                                                                                |

## Adding authentik as a server provider with your IDP

This will depend heavily on what software you are using for your IDP. On the Metadata tab in the SAML Federation Source you can download the metadata for the service provider, this should enable you to import this into most IDPs. If this does not work, the important parts are:

- Entity ID: Taken from the Issuer/Entity ID field above
- Return URL/ACS URL: `https://authentik.company/source/saml/<source-slug>/acs/`
- Certificate: If you have chosen to sign your outgoing requests, use the public side of the certificate that you specified in the settings

## Example IDP metadata

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
