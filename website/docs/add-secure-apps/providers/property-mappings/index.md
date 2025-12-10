---
title: Provider property mappings
---

Property mappings allow you to pass information to external applications. For example, pass the current user's groups as a SAML parameter.

## SAML property mappings

SAML property mappings allow you embed information into the SAML authentication request. This information can then be used by the application to, for example, assign permissions to the object.

## Scope mappings with OAuth2

Scope mappings are used by the OAuth2 provider to map information from authentik to OAuth2/OIDC claims. Values returned by a scope mapping are added as custom claims to access and ID tokens.

:::info Default value for `email_verified`
By default, authentik sets the `email_verified` claim to `False`, since it has no way to confirm whether a user's email is verified. Setting this claim to `True` by default could introduce unintended security risks.

Be aware that some applications might require this claim to be true to successfully authenticate users. In this case you should create a custom email scope mapping that returns `email_verified` as `True`, using the following expression:

```
return {
    "email": user.email,
    "email_verified": True,
}
```

:::

## Skip objects during synchronization

To skip synchronization for a specific object, you can create a property mapping with an expression that triggers the `SkipObject` exception. This functionality is supported by the following providers: [**Google Workspace**](../gws/), [**Microsoft Entra ID**](../entra/), and [**SCIM**](../scim/).

**Example:**

```python
if request.user.username == "example_username":
	raise SkipObject
```
