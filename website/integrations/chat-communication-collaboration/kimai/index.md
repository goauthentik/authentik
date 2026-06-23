---
title: Integrate with Kimai
sidebar_label: Kimai
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Kimai?

> Kimai is a free and open source time-tracking application for recording work time and reporting it by customer, project, activity, and user.
>
> -- https://www.kimai.org/

## Preparation

The following placeholders are used in this guide:

- `kimai.company` is the FQDN of the Kimai installation.
- `authentik.company` is the FQDN of the authentik installation.
- `admin.group` is the name of the authentik group whose members should receive the Kimai administrator role.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Kimai with authentik, you need to create an application/provider pair in authentik.

Kimai imports SAML users during their first login. To assign Kimai roles from authentik group membership, configure the role mappings in the Kimai `local.yaml` file in the next section.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://kimai.company/auth/saml/acs`.
        - Set the **SLS URL** to `https://kimai.company/auth/saml/logout`.
        - Set the **Audience** to `https://kimai.company/auth/saml/metadata`.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing certificate**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
            - Set **Default NameID Policy** to **Email address**.
    - **Configure Bindings** _(optional)_: create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to control which users can access the Kimai application from the **Application Dashboard** page.

3. Click **Submit**.

### Download the signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the newly created Kimai provider.
3. Under **Related objects** > **Download signing certificate**, click **Download**. The certificate content is required in the next section.

## Kimai configuration

Paste the following block in your `local.yaml` file, after replacing the placeholder values from above. The file is usually located in `/opt/kimai/config/packages/local.yaml`.

For `x509cert`, open the authentik signing certificate in a text editor, remove the `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` lines, remove line breaks, and paste the remaining certificate content.

<!-- prettier-ignore-start -->

```yaml title="/opt/kimai/config/packages/local.yaml"
kimai:
    saml:
        activate: true
        title: Log in with authentik
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
            idp:
                entityId: "https://authentik.company/application/saml/<application_slug>/metadata/"
                singleSignOnService:
                    url: "https://authentik.company/application/saml/<application_slug>/"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                # the "single logout" feature was not yet tested, if you want to help, please let me know!
                singleLogoutService:
                    url: "https://authentik.company/application/saml/<application_slug>/"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                x509cert: "<certificate contents from authentik>"
            sp:
                entityId: "https://kimai.company/auth/saml/metadata"
                assertionConsumerService:
                    url: "https://kimai.company/auth/saml/acs"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                singleLogoutService:
                    url: "https://kimai.company/auth/saml/logout"
                    binding: "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
```

<!-- prettier-ignore-end -->

Afterwards, rebuild the Kimai cache or restart the Docker container.

## Configuration verification

To confirm that authentik is properly configured with Kimai, open Kimai, log out, and click **Log in with authentik**. You should be redirected to authentik to log in and then redirected back to Kimai.

## Resources

- [Kimai SAML documentation](https://www.kimai.org/documentation/saml.html)
- [Kimai Authentik SAML documentation](https://www.kimai.org/documentation/saml-authentik.html)
