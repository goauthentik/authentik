---
title: Integrate with SonarQube
sidebar_label: SonarQube
---

<span className="badge badge--primary">Support level: Community</span>

## What is SonarQube

> Self-managed static analysis tool for continuous codebase inspection
>
> -- https://www.sonarsource.com/products/sonarqube/

## Preparation

The following placeholders are used in this guide:

- `sonarqube.company` is the FQDN of the sonarqube installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## Terraform provider

Create an application in authentik. Create a SAML Provider with the following values

```hcl

data "authentik_flow" "default-provider-authorization-implicit-consent" {
  slug = "default-provider-authorization-implicit-consent"
}

data "authentik_property_mapping_saml" "saml-sonar-qube" {
  managed_list = [
    "goauthentik.io/providers/saml/email",
    "goauthentik.io/providers/saml/username",
    "goauthentik.io/providers/saml/name"
  ]
}

resource "authentik_provider_saml" "provider_sonar-qube" {
    name                = "SonarQube"

    authorization_flow  = data.authentik_flow.default-provider-authorization-implicit-consent.id

    acs_url    = "https://sonarqube.company/oauth2/callback/saml"
    issuer     = "https://authentik.company/"
    sp_binding = "post"
    audience   = "https://sonarqube.company/saml2/metadata"

    property_mappings = data.authentik_property_mapping_saml.saml-sonar-qube.ids
}

resource "authentik_application" "application_sonar-qube" {
    name              = "SonarQube"
    slug              = "sonarqube"
    protocol_provider = authentik_provider_saml.provider_sonar-qube.id
}

```

## SonarQube

Navigate to Administration -> Configuration -> Authentication -> Saml

Input these Values

- Application ID: https://sonarqube.company/saml2/metadata
- Provider Name: authentik
- Provider ID: https://authentik.company/
- SAML login url: https://authentik.company/application/saml/sonarqube/sso/binding/redirect/
- Identity provider certificate: Download it from authentik
- SAML user login attribute: http://schemas.goauthentik.io/2021/02/saml/username
- SAML user name attribute: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name
- SAML user email attribute: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress
