---
title: Overview
---

Property Mappings allow you to pass information to external applications. For example, pass the current user's groups as a SAML parameter. Property Mappings are also used to map Source fields to authentik fields, for example when using LDAP.

## SAML Property Mapping

SAML Property Mappings allow you embed information into the SAML AuthN request. This information can then be used by the application to, for example, assign permissions to the object.

## LDAP Property Mapping

LDAP Property Mappings are used when you define a LDAP Source. These mappings define which LDAP property maps to which authentik property. By default, the following mappings are created:

-   authentik default Active Directory Mapping: givenName
-   authentik default Active Directory Mapping: sAMAccountName
-   authentik default Active Directory Mapping: sn
-   authentik default Active Directory Mapping: userPrincipalName
-   authentik default LDAP Mapping: mail
-   authentik default LDAP Mapping: Name
-   authentik default OpenLDAP Mapping: cn
-   authentik default OpenLDAP Mapping: uid

These are configured with most common LDAP setups.

### Custom LDAP Property Mapping 

If the default source mapping is not enough, you can set your own custom property mapping. 

For example the setting `ldap-displayName-mapping:name`  means that the ldap source field `displayName` will be mapped to the `name` field in authentik. 

Here are the steps:

1. In authentik, open the Admin interface, and then navigate to **Customization -> Property Mappings**.
2. Click `Create`, select `LDAP Property Mapping` and then click `Next`.
3. Type a unique and meaningful `Name`, such as `ldap-displayName-mapping:name`.
4. Type authentik inner field in `Object field`. such as `name`. If you want to add more extend attributes, you can type `attributes.mobile` for example.
5. Type `Expression` which will get value from LDAP source. e.g. `return list_flatten(ldap.get("displayName"))`.

`list_flatten(["input string array"])` will convert string array to single string. If you are not sure whether the ldap field is an array or not, you may map the field to any `attributes.xxx` and then check the sync result in authentik UI.

## Scope Mapping

Scope Mappings are used by the OAuth2 Provider to map information from authentik to OAuth2/OpenID Claims. Values returned by a Scope Mapping are added as custom claims to Access and ID tokens.
