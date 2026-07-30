---
title: Integrate with PowerDNS-Admin
sidebar_label: PowerDNS-Admin
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is PowerDNS-Admin?

> A PowerDNS web interface with advanced features.
>
> -- https://github.com/ngoduykhanh/PowerDNS-Admin

## Preparation

The following placeholders are used in this guide:

- `pdns-admin.company` is the FQDN of the PowerDNS-Admin installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of PowerDNS-Admin with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://pdns-admin.company/saml/authorized`.
        - Set the **Audience** to `pdns-admin`.
        - Under **Advanced protocol settings**, select an available **Signing certificate**.
        - Under **Advanced protocol settings**, select all managed SAML property mappings.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## PowerDNS-Admin configuration

For Docker-based installations, set the following environment variables:

```env title=".env"
SAML_ENABLED=True
SAML_PATH=os.path.join(os.path.dirname(file), 'saml')
SAML_METADATA_URL=https://authentik.company/application/saml/<application_slug>/metadata/
SAML_METADATA_CACHE_LIFETIME=1
SAML_LOGOUT_URL=https://authentik.company/application/saml/<application_slug>/
SAML_SP_ENTITY_ID=pdns-admin
SAML_SP_CONTACT_NAME=me
SAML_SP_CONTACT_MAIL=me
SAML_NAMEID_FORMAT=urn:oasis:names:tc:SAML:2.0:nameid-format:persistent
SAML_ATTRIBUTE_USERNAME=http://schemas.goauthentik.io/2021/02/saml/username
SAML_ATTRIBUTE_NAME=http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name
SAML_ATTRIBUTE_EMAIL=http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress
SAML_ATTRIBUTE_GROUP=http://schemas.xmlsoap.org/claims/Group
SAML_GROUP_ADMIN_NAME=<admin-group-name>
SAML_SIGN_REQUEST='False'
SAML_ASSERTION_ENCRYPTED=False
SAML_WANT_MESSAGE_SIGNED=False
SAML_CERT=/saml.crt
```

Mount the signing certificate selected in authentik as a file in the Docker container. The path in the container must match the path configured in `SAML_CERT`.

For example:

```yaml title="docker-compose.yml"
services:
    powerdns-admin:
        image: powerdnsadmin/pda-legacy:latest
        restart: always
        ports:
            - 80:80
        volumes:
            - ./saml.crt:/saml.crt:ro
```

Restart PowerDNS-Admin for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with PowerDNS-Admin, log out and log back in through authentik.

## Resources

- [PowerDNS-Admin GitHub repository](https://github.com/PowerDNS-Admin/PowerDNS-Admin)
- [PowerDNS-Admin environment variables](https://github.com/PowerDNS-Admin/PowerDNS-Admin/blob/master/docs/wiki/configuration/Environment-variables.md)
