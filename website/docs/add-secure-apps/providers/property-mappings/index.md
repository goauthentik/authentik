---
title: Provider property mappings
---

Property mappings allow you to pass information to external applications. For example, pass the current user's groups as a SAML parameter.

## SAML property mappings

SAML property mappings allow you embed information into the SAML authentication request. This information can then be used by the application to, for example, assign permissions to the object.

## Scope mappings with OAuth2

Scope mappings are used by the OAuth2 provider to map information from authentik to OAuth2/OIDC claims. Values returned by a scope mapping are added as custom claims to access and ID tokens.

:::info `email_verified` claim default value
Because authentik doesn;t have a single source to state whether a users' email is verified or not, and claiming that it is verified could lead to security implications, by default we set this claim to false.

Be aware that some applications might require this claim to be true to successfully authenticate users. In this case you can create a custom email scope mapping that returns `email_verified` as true.
:::

## Skip objects during synchronization

To skip synchronization for a specific object, you can create a property mapping with an expression that triggers the `SkipObject` exception. This functionality is supported by the following providers: [**Google Workspace**](../gws/), [**Microsoft Entra ID**](../entra/), and [**SCIM**](../scim/).

**Example:**

```python
if request.user.username == "example_username":
	raise SkipObject
```
