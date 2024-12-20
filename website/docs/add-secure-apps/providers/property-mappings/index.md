---
title: Provider property mappings
---

Property mappings allow you to pass information to external applications. For example, pass the current user's groups as a SAML parameter.

## SAML property mappings

SAML property mappings allow you embed information into the SAML authentication request. This information can then be used by the application to, for example, assign permissions to the object.

## Scope mappings

Scope mappings are used by the OAuth2 provider to map information from authentik to OAuth2/OpenID claims. Values returned by a scope mapping are added as custom claims to access and ID tokens.
