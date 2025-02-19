---
title: Integrate with PowerDNS-Admin
sidebar_label: PowerDNS-Admin
---

# Integrate with PowerDNS-Admin

<span class="badge badge--secondary">Support level: Community</span>

## What is PowerDNS-Admin

> A PowerDNS web interface with advanced features.
>
> -- https://github.com/ngoduykhanh/PowerDNS-Admin

## Preparation

The following placeholders are used in this guide:

- `pdns-admin.company` is the FQDN of the PowerDNS-Admin installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Create a SAML provider with the following parameters:

- ACS URL: `https://pdns-admin.company/saml/authorized`
- Issuer: `https://authentik.company`
- Service Provider Binding: `Post`
- Audience: `pdns-admin`
- Signing Keypair: Select any certificate you have.
- Property mappings: Select all Managed mappings.

You can of course use a custom signing certificate, and adjust durations.

## PowerDNS-Admin

You need to set the following `env` Variables for Docker based installations.

Set the following values:

```env
SAML_ENABLED=True
SAML_PATH=os.path.join(os.path.dirname(file), 'saml')
SAML_METADATA_URL=https://authentik.company/application/saml/<application-slug>/metadata/
SAML_METADATA_CACHE_LIFETIME=1
SAML_LOGOUT_URL=https://authentik.company/application/saml/<application-slug>/slo/binding/redirect/
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

You must mount the certificate selected in authentik as a file in the Docker container. The path in the container must match the path in the env variable `SAML_CERT`.

### docker-compose

```yaml
services:
    powerdns-admin:
        image: powerdnsadmin/pda-legacy:latest
        restart: always
        ports:
            - 80:80
        volumes:
            - ./saml.crt:/saml.crt:ro
```
