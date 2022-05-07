---
title: SAML
---

## SAML Source

This source allows authentik to act as a SAML Service Provider. Just like the SAML Provider, it supports signed requests. Vendor-specific documentation can be found in the Integrations Section.

## Example setup
If you have the provider metadata, you should be able to extract all values you need from this. There is an example provided for a basic IDP metadata file below.

### Name/slug
Whatever you want the source to be called

### SSO URL
This would be the SingleSignOnService URL for the provider (https://federation.example.com/login/saml). The metadata sometimes contains multiple URLs with different bindings (HTTP-Redirect and HTTP-POST), choose the URL corresponding to the chosen Binding Type.

### SLO URL
Not all providers support this, if supported and supplied can log you out of the identity provider at the same time as you log out from Authentik.

### Issuer / Entity ID
This is the Issuer/Entity ID on the Authentik side. You can more or less choose what you want, a recommendation is to choose the URL of the Authentik instance (e.g. https://authentik.example.com/) since this will identify the service provider on the other side.

### Binding Type
The binding type of the SSO URL. There are two main types, HTTP-Redirect (GET) and HTTP-POST, this will depend on what your Identity Provider has support for.

### Other settings
The rest of the settings usually don't need changing and have sane defaults. There are some exceptions:

- Depending on what your Identity Provider uses as persistent ID you might need to change the NameID Policy to get the result you want. Some Identity Providers use a hashed or random value per user and some rely on the email or username as a unique identifier. If it is a hashed value, the users will receive a random string of numbers and letters as the username, you can then change the NameID Policy to "Email address" to create users in Authentik based on that instead

- Allow IDP-Initiated Logins: Allows the user to be authenticated automatically from the IDP side, without interaction with the Authentik logon screen. Since this request ist not verified, this might be a security concern if a third party initiates an authentication on behalf of a user.

- Flow settings: If you have build your own authentication flows, change to use them here.

### Adding authentik as a server provider with your IDP
This will depend heavily on what software you are using on your Identity Provider. On the Metadata tab in the SAML Federation Source you can download the metadata for the service provider, this should enable you to import this into most Identity Providers. If this does not work, the important parts are:

- Entity ID: Taken from the Issuer/Entity ID field above
- Return URL/Assertion Consumer Service URL/ACS: https://authentik.example.com/source/saml/[source-slug]/acs/
- Certificate: If you have chosen to sign your outgoing requests, use the public side of the certificate that you specified in the settings

### Example metadata
```xml
<md:EntityDescriptor entityID="https://federation.example.com/idp">
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
        <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" Location="https://federation.example.com/login/saml/"/>
        <md:SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" Location="https://federation.example.com/login/saml/"/>
    </md:IDPSSODescriptor>
    <md:Organization>
        <md:OrganizationName xml:lang="en">Example Organization</md:OrganizationName>
        <md:OrganizationDisplayName xml:lang="en">Example Organization</md:OrganizationDisplayName>
        <md:OrganizationURL xml:lang="en">http://www.example.com</md:OrganizationURL>
    </md:Organization>
    <md:ContactPerson contactType="technical">
        <md:Company>Example Organization</md:Company>
        <md:GivenName>John</md:GivenName>
        <md:SurName>Doe</md:SurName>
        <md:EmailAddress>john.doe@example.com</md:EmailAddress>
        <md:TelephoneNumber>012 345 67890</md:TelephoneNumber>
    </md:ContactPerson>
    <md:ContactPerson contactType="support">
        <md:Company>Example Organization</md:Company>
        <md:GivenName>Helpdesk</md:GivenName>
        <md:SurName>Support</md:SurName>
        <md:EmailAddress>helpdesk@example.com</md:EmailAddress>
        <md:TelephoneNumber>012 345 67890</md:TelephoneNumber>
    </md:ContactPerson>
</md:EntityDescriptor>
```