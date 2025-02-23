---
title: Integrate with Weblate
sidebar_label: Weblate
support_level: community
---

## What is Weblate

> Weblate is a copylefted libre software web-based continuous localization system, used by over 2500 libre projects and companies in more than 165 countries.
>
> -- https://weblate.org/en/

## Preparation

The following placeholders are used in this guide:

- `weblate.company` is the FQDN of the Weblate installation.
- `authentik.company` is the FQDN of the authentik installation.
- `weblate-slug` is the slug of the Weblate application.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Weblate with authentik, you need to create an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create four **SAML Provider Property Mapping**s with the following settings:
    - **Full Name Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: <kbd>urn:oid:2.5.4.3</kbd>
        - **Friendly Name**: Leave blank
        - **Expression**:
        ```python
        return request.user.name
        ```
    - **OID_USERID Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: <kbd>urn:oid:0.9.2342.19200300.100.1.1</kbd>
        - **Friendly Name**: Leave blank
        - **Expression**:
        ```python
        return request.user.username
        ```
    - **Username Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: <kbd>username</kbd>
        - **Friendly Name**: Leave blank
        - **Expression**:
        ```python
        return request.user.username
        ```
    - **Email Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: <kbd>email</kbd>
        - **Friendly Name**: Leave blank
        - **Expression**:
        ```python
        return request.user.email
        ```

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to <kbd>https://<em>weblate.company</em>/accounts/complete/saml/</kbd>.
    - Set the **Audience** to <kbd>https://<em>weblate.company</em>/accounts/metadata/saml/</kbd>.
    - Set the **Issuer** to <kbd>https://<em>authentik.company</em>/application/saml/<em>application-slug</em>/sso/binding/redirect/</kbd>.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, select an available signing certificate. Then, under **Property mappings**, add the ones you just created.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Weblate configuration

The variables below need to be set, depending on if you deploy in a container or not you can take a look at the following links

- https://docs.weblate.org/en/latest/admin/config.html#config
- https://docs.weblate.org/en/latest/admin/install/docker.html#docker-environment

Variables to set

- ENABLE_HTTPS: `1`
- SAML_IDP_ENTITY_ID: `https://authentik.company/application/saml/weblate-slug/sso/binding/redirect/`
- SAML_IDP_URL: `https://authentik.company/application/saml/weblate-slug/sso/binding/redirect/`
- SAML_IDP_X509CERT: `MIIFDjCCAvagAwIBAgIRAJV8hH0wGkhGvbhhDKppWIYwDQYJKoZIhvcNAQELBQAw....F9lT9hHwHhsnA=`

The `SAML_IDP_X509CERT` is the certificate in the SAML Metadata `X509Certificate` key.

Should you wish to only allow registration and login through Authentik, you should set the following variables as well.

- REGISTRATION_OPEN: `0`
- REGISTRATION_ALLOW_BACKENDS: `saml`
- REQUIRE_LOGIN: `1`
- NO_EMAIL_AUTH: `1`

Should you wish to deploy this in a container prefix all the variables with `WEBLATE_` and set them as environment variables
