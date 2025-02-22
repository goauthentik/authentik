---
title: Integrate with Zammad
sidebar_label: Zammad
support_level: community
---

## What is Zammad

> Zammad is a web-based, open source user support/ticketing solution.
> Download and install it on your own servers. For free.
>
> -- https://zammad.org/

## Preparation

The following placeholders are used in this guide:

- `zammad.company` is the FQDN of the Zammad installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik Configuration

### Step 1 - Property Mappings

Create two Mappings (under _Customization/Property Mappings_) with these settings:

#### name mapping

- Name: Zammad SAML Mapping: name
- SAML Attribute Name: name
- Friendly Name: none
- Expression: `return request.user.name`

#### email mapping

- Name: Zammad SAML Mapping: email
- SAML Attribute Name: email
- Friendly Name: none
- Expression: `return request.user.email`

### Step 2 - SAML Provider

In authentik, create a SAML Provider (under _Applications/Providers_) with these settings :

- Name : zammad
- ACS URL: `https://zammad.company/auth/saml/callback`
- Issuer: `https://zammad.company/auth/saml/metadata`
- Service Provider Binding: Post
- Audience: `https://zammad.company/auth/saml/metadata`
- Property mappings: Zammad SAML Mapping: name & Zammad SAML Mapping: email
- NameID Property Mapping: Zammad SAML Mapping: name

### Step 3 - Application

In authentik, create an application (under _Resources/Applications_) with these settings :

- Name: Zammad
- Slug: zammad
- Provider: zammad

## zammad Setup

Configure Zammad SAML settings by going to settings (the gear icon), and selecting `Security -> Third-party Applications` and activate `Authentication via SAML` and change the following fields:

- Display name: authentik
- IDP SSO target URL: https://authentik.company/application/saml/zammad/sso/binding/init/
- IDP single logout target URL: https://zammad.company/auth/saml/slo
- IDP certificate: ----BEGIN CERTIFICATE---- …
- IDP certificate fingerprint: empty
- Name Identifier Format: empty

## Additional Resources

- https://admin-docs.zammad.org/en/latest/settings/security/third-party/saml.html
- https://community.zammad.org/t/saml-authentication-with-authentik-saml-login-url-and-auto-assign-permission/10876/3
