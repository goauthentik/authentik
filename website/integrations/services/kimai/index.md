---
title: Integrate with Kimai
sidebar_label: Kimai
support_level: community
---

## What is Kimai

> Kimai is a free & open source timetracker. It tracks work time and prints out a summary of your activities on demand. Yearly, monthly, daily, by customer, by project … Its simplicity is its strength. Due to Kimai's browser based interface it runs cross-platform, even on your mobile device.
>
> -- https://www.kimai.org/about/

## Preparation

The following placeholders are used in this guide:

- `kimai.company` is the FQDN of the Kimai Install
- `authentik.company` is the FQDN of the authentik Install
- `admin.group` is the authentik group to be made Admin in Kimai

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Kimai with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to <kbd>https://<em>kimai.company</em>/auth/saml/acs</kbd>.
    - Set the **Audience** to <kbd>https://<em>kimai.company</em>auth/saml</kbd>.
    - Set the **Issuer** to <kbd>https://<em>authentik.company</em></kbd>.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, select an available signing certificate.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

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
