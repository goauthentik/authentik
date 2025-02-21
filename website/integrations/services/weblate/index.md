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

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

- ACS URL: `https://weblate.company/accounts/complete/saml/`
- Audience: `https://weblate.company/accounts/metadata/saml/`
- Service Provider Binding: Post
- Issuer: `https://authentik.company/application/saml/weblate-slug/sso/binding/redirect/`

You can of course use a custom signing certificate, and adjust durations.

## Property mappings

We need to create some property mappings so our application will work. After you create the property mappings, assign them to the provider.

### Full name

- Name: `Weblate - Full name`
- SAML Attribute Name: `urn:oid:2.5.4.3`
- Expression

```python
return request.user.name
```

### OID_USERID

- Name: `Weblate - OID_USERID`
- SAML Attribute Name: `urn:oid:0.9.2342.19200300.100.1.1`
- Expression

```python
return request.user.username
```

### Username

- Name: `Weblate - Username`
- SAML Attribute Name: `username`
- Expression

```python
return request.user.username
```

### Email

- Name: `Weblate - Email`
- SAML Attribute Name: `email`
- Expression

```python
return request.user.email
```

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
