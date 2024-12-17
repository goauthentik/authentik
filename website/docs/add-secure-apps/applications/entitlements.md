---
title: Application Entitlements (authentik 2024.12+)
sidebar_label: Application Entitlements
---

# Application Entitlements

<span class="badge badge--preview">Preview</span>
<span class="badge badge--version">authentik 2024.12+</span>

---

Application entitlements can be used to manage authorization within an application through authentik. Entitlements are scoped to a single application and can be bound to multiple users/groups (binding policies is not currently supported), giving them access to the entitlement. An application can either check for the name of the entitlement (via the [`entitlements` scope](../providers/oauth2/index.md#default--special-scopes)), or via attributes stored in entitlements.

As entitlements exist within an application, names of entitlements must be unique within an application. Entitlements can be created via the Admin interface by clicking on an application and selecting the _Application entitlements_ tab, or via the API. This also means that entitlements are deleted when an application is deleted.

## Using entitlements

Entitlements a user has access to can be retrieved using the `user.app_entitlements()` function in property mappings/policies. This function needs to be passed the application to get the entitlements for, for example:

```python
entitlements = [entitlement.name for entitlement in request.user.app_entitlements(provider.application)]
return {
    "entitlements": entitlements,
}
```

## Attributes

Each entitlement can store attributes similar to user and group attributes. These attributes can be accessed in property mappings and passed to applications via `user.app_entitlements_attributes`, for example:

```python
attrs = request.user.app_entitlements(provider.application)
return {
    "my_attr": attrs.get("my_attr")
}
```
