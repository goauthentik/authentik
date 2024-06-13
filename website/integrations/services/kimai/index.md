---
title: Kimai
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Kimai

> Kimai is a free & open source timetracker. It tracks work time and prints out a summary of your activities on demand. Yearly, monthly, daily, by customer, by project … Its simplicity is its strength. Due to Kimai's browser based interface it runs cross-platform, even on your mobile device.
>
> -- https://www.kimai.org/about/

## Preparation

The following placeholders will be used:

-   `kimai.company` is the FQDN of the Kimai Install
-   `authentik.company` is the FQDN of the authentik Install
-   `admin.group` is the authentik group to be made Admin in Kimai

Create an application in authentik and use the slug for later as `<application-slug>`.

Create a SAML provider with the following parameters:

-   ACS URL: `https://kimai.company/auth/saml/acs`
-   Audience: `https://kimai.company/auth/saml`
-   Issuer: `https://authentik.company`
-   Binding: `Post`

Under _Advanced protocol settings_, set a certificate for _Signing Certificate_.

## Kimai Configuration

Paste the following block in your `local.yaml` file, after replacing the placeholder values from above. The file is usually located in `/opt/kimai/config/packages/local.yaml`.

To get the value for `x509cert`, go to _System_ > _Certificates_, and download the public Signing Certificate. To avoid further problems, concat it into "string format" using e.g.: https://www.samltool.com/format_x509cert.php

```yaml
# Optionally add this for docker debug-logging
# monolog:
#   handlers:
#     main:
#       path: php://stderr

kimai:
    saml:
        activate: true
        title: Login with authentik
        mapping:
            - {
                  saml: $http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress,
                  kimai: email,
              }
            - {
                  saml: $http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name,
                  kimai: alias,
              }
        roles:
            attribute: http://schemas.xmlsoap.org/claims/Group
            mapping:
                # Insert your roles here (ROLE_USER is added automatically)
                - { saml: admin.group, kimai: ROLE_ADMIN }
        connection:
            # You SAML provider
            # Your authentik instance, replace https://authentik.company with your authentik URL
            idp:
                entityId: "https://authentik.company/"
                singleSignOnService:
                    url: "https://authentik.company/application/saml/<application-slug>/sso/binding/redirect/"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                # the "single logout" feature was not yet tested, if you want to help, please let me know!
                singleLogoutService:
                    url: "https://authentik.company/application/saml/<application-slug>/slo/binding/redirect/"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                # Signing certificate from *Advanced protocol settings*
                x509cert: "XXXXXXXXXXXXXXXXXXXXXXXXXXX=="
            # Service Provider Data that we are deploying.
            # Your Kimai instance, replace https://kimai.company with your Kimai URL
            sp:
                entityId: "https://kimai.company/"
                assertionConsumerService:
                    url: "https://kimai.company/auth/saml/acs"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                singleLogoutService:
                    url: "https://kimai.company/auth/saml/logout"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                #privateKey: ''
            # only set baseurl, if auto-detection doesn't work
            baseurl: "https://kimai.company/auth/saml/"
            strict: false
            debug: true
            security:
                nameIdEncrypted: false
                authnRequestsSigned: false
                logoutRequestSigned: false
                logoutResponseSigned: false
                wantMessagesSigned: false
                wantAssertionsSigned: false
                wantNameIdEncrypted: false
                requestedAuthnContext: true
                signMetadata: false
                wantXMLValidation: true
                signatureAlgorithm: "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
                digestAlgorithm: "http://www.w3.org/2001/04/xmlenc#sha256"
            contactPerson:
                technical:
                    givenName: "Kimai Admin"
                    emailAddress: "admin@example.com"
            organization:
                en:
                    name: "Kimai"
                    displayname: "Kimai"
                    url: "https://kimai.company"
```

Afterwards, either [rebuild the cache](https://www.kimai.org/documentation/cache.html) or restart the docker container.
