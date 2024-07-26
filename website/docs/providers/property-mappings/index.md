---
title: Property Mappings
---

Property Mappings allow you to pass information to external applications. For example, pass the current user's groups as a SAML parameter.

## SAML Property Mapping

SAML Property Mappings allow you embed information into the SAML AuthN request. This information can then be used by the application to, for example, assign permissions to the object.

## Scope Mapping

Scope Mappings are used by the OAuth2 Provider to map information from authentik to OAuth2/OpenID Claims. Values returned by a Scope Mapping are added as custom claims to Access and ID tokens.
