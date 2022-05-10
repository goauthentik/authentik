---
title: SAML
---

## SAML Source

This source allows authentik to act as a SAML Service Provider. Just like the SAML Provider, it supports signed requests. Vendor-specific documentation can be found in the Integrations Section.

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
| SSO URL                    | https://saml.company/login/saml  | The SingleSignOnService URL for the IDP, this can be found in the metadata or IDP documentation. There can be different URLs for different Binding Types (e.g. HTTP-Redirect and HTTP-POST), use the URL corresponding to the binding type you choose below                    |
| SLO URL                    | https://saml.company/logout/saml | The URL that is called when a user logs out of authentik, can be used to automatically log the user out of the SAML IDP after logging out of Authentik. Not supported by all IDPs, and not always wanted behaviour.                                                            |
| Issuer/Entity ID           | https://authentik.company        | The identifier for the authentik instance in the SAML federation, can be chosen freely. This is used to identify the SP on the IDP side, it usually makes sense to configure this to the URL of the SP or the path corresponding to the SP (e.g. `/source/saml/<source-slug>/` |
| Binding Type               | HTTP-POST                        | How authentik communicates with the SSO URL (302 redirect or POST request). This will depend on what the provider supports.                                                                                                                                                    |
| Allow IDP-Initiated Logins | False                            | Whether to allow the IDP to log users into authentik without any interaction. Activating this may constitute a security risk since this request is not verified, and could be utilised by an attacker to authenticate a user without interaction on their side.                |
| NameID Policy              | Persistent                       | Depending on what the IDP sends as persistent ID, some IDPs use the username or email address while others will use a random string/hashed value. If the user in authentik receives a random string as a username, try using Email address or Windows                          |
| Flow settings              | Default                          | If there are custom flows in your instance for external authentication, change to use them here                                                                                                                                                                                |

## Adding authentik as a server provider with your IDP

This will depend heavily on what software you are using for your IDP. On the Metadata tab in the SAML Federation Source you can download the metadata for the service provider, this should enable you to import this into most IDPs. If this does not work, the important parts are:

-   Entity ID: Taken from the Issuer/Entity ID field above
-   Return URL/ACS URL: `https://authentik.company/source/saml/<source-slug>/acs/`
-   Certificate: If you have chosen to sign your outgoing requests, use the public side of the certificate that you specified in the settings

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
