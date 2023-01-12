---
title: Overview
---

Property Mappings allow you to pass information to external applications. For example, pass the current user's groups as a SAML parameter. Property Mappings are also used to map Source fields to authentik fields, for example when using LDAP.

## SAML Property Mapping

SAML Property Mappings allow you embed information into the SAML AuthN request. This information can then be used by the application to, for example, assign permissions to the object.

## LDAP Property Mapping

LDAP Property Mappings are used when you define a LDAP Source. These mappings define which LDAP property maps to which authentik property. By default, the following mappings are created:

-   authentik default Active Directory Mapping: active
-   authentik default Active Directory Mapping: givenName
-   authentik default Active Directory Mapping: sAMAccountName
-   authentik default Active Directory Mapping: sn
-   authentik default Active Directory Mapping: userPrincipalName
-   authentik default LDAP Mapping: mail
-   authentik default LDAP Mapping: Name
-   authentik default OpenLDAP Mapping: cn
-   authentik default OpenLDAP Mapping: uid

These are configured with most common LDAP setups.

## Scope Mapping

Scope Mappings are used by the OAuth2 Provider to map information from authentik to OAuth2/OpenID Claims. Values returned by a Scope Mapping are added as custom claims to Access and ID tokens.
