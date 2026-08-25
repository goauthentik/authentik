---
title: Source property mappings
---

Source property mappings allow you to modify or gather extra information from sources.

This page is an overview of how property mappings work. For information about a specific protocol, refer to the protocol page:

- [Kerberos](../protocols/kerberos/#kerberos-source-property-mappings)
- [LDAP](../protocols/ldap/index.md#ldap-source-property-mappings)
- [OAuth](../protocols/oauth/index.mdx#oauth-source-property-mappings)
- [SAML](../protocols/saml/index.md#saml-source-property-mappings)
- [SCIM](../protocols/scim/index.md#scim-source-property-mappings)

## Create a custom source property mapping

If the default source mappings are not enough, or if you need to get additional data from the source, you can create your own custom source property mappings.

Here are the steps:

1. In authentik, open the Admin interface, and then navigate to **Customization** > **Property Mappings**.
2. Click **Create**, select the property mapping type for your source, and then click **Next**.
3. Type a unique and meaningful **Name**, such as `ldap-displayName-mapping:name`.
4. In the **Expression** field, enter Python expressions to retrieve the value from the source. See [Expression semantics](#expression-semantics) below for details.
5. In the source configuration, select the newly created property mapping as a **User property mapping** if it applies to users, or **Group property mapping** if it applies to groups.

## How it works

### Expression semantics

Each source provides the Python expression with additional data. You can import parts of that data into authentik users and groups. Assuming the source provides us with a `data` Python dictionary, you can write the following:

```python
return {
    "name": data.get("displayName"),
}
```

You can see that the expression returns a Python dictionary. The dictionary keys must match [User properties](../../user/user_ref.mdx#object-properties) or [Group properties](../../groups/group_ref.md#object-properties). Note that `group_attributes` cannot be set for users. A source user property mapping can return `groups` to synchronize source groups as described in [Group synchronization](#group-synchronization); it does not set a regular user object property.

See each source documentation for a reference of the available data. See the authentik [expressions documentation](./expressions.md) for available data and functions.

Note that the [`list_flatten`](./expressions.md#list_flattenvalue-listany--any---optionalany) method is applied for all top-level properties, but not for attributes:

```python
return {
    "username": data.get("username"), # list_flatten is automatically applied to top-level attributes
    "attributes": {
        "phone": list_flatten(data.get("phoneNumber")), # but not for attributes!
    },
}
```

### Object construction process

A user or group object is constructed as follows:

1.  The source provides initial properties based on commonly used data.
2.  Each property mapping associated with the source is run and results are merged into the previous properties.
    - If a property mapping throws an error, the process is aborted. If that happens inside a synchronization process, the object is skipped. If it happens during an enrollment or authentication flow, the flow is canceled.
    - If a property mapping sets one attribute to `None`, that attribute is then discarded.
3.  If the `username` field is not set for user objects, or the `name` field is not set for group objects, the process is aborted.
4.  The object is created or updated. The `attributes` property is merged with existing data if the object already exists.

### Group synchronization

LDAP and SCIM sources have built-in mechanisms to get groups. This section does not apply to them.

You can write a custom property mapping to set the user's groups:

```python
return {
    "groups": data.get("groups", []),
}
```

The `groups` attribute is a special attribute that must contain group identifiers. By default, those identifiers are also used as the group name. Each identifier is then given to group property mappings as the `group_id` variable, if extra processing needs to happen.

An identifier has to be a simple value such as a string. Entries that are not, such as the objects some identity providers return in an OpenID Connect `groups` claim, are skipped, and a **Configuration error** event records how many were dropped.

#### Object-shaped OpenID Connect group claims

The OpenID Connect standard does not define a standard `groups` claim or its value shape. Some identity providers return group objects instead of simple identifiers.

The cleanest solution is to configure the identity provider to return an array of stable, unique identifiers:

```json
{
    "groups": ["g1", "g2"]
}
```

Use an immutable provider group ID where possible. Do not use a display name as the identifier unless it is guaranteed to be unique and stable.

If the provider cannot return identifier values directly, create an OAuth source property mapping and attach it to the source's **User property mappings**. OAuth source property mappings receive the provider response data in the `info` variable.

The following mapping supports an array-valued `groups` claim containing simple identifiers, objects, or both. It preserves simple identifier entries and extracts identifiers from object entries:

```python
groups = []

for group in info.get("groups", []):
    if isinstance(group, dict):
        # Replace these member names with those used by your provider.
        # For example, some providers use "id"; SCIM group resources use "value".
        group_id = group.get("value") or group.get("id")
    else:
        group_id = group

    if group_id is None:
        continue

    try:
        hash(group_id)
    except TypeError:
        continue

    groups.append(group_id)

return {"groups": groups}
```

Select a stable, unique identifier from each object because authentik uses it to recognize the synchronized group.

The property mapping adds extracted identifiers to the source's initial `groups` property. List properties are merged rather than replaced, so the original object-shaped entries remain.

authentik skips the original unhashable entries and records a **Configuration error** event. The extracted identifiers can still synchronize successfully, but this mapping does not remove the event.

To avoid the event entirely, configure the provider to return identifier values in the `groups` claim. Alternatively, configure the provider to emit an identifier-only claim, map that claim to `groups`, and ensure that the original `groups` claim is absent or also contains only identifier values.

Optionally, create another OAuth source property mapping and attach it to the source's **Group property mappings** to recover the provider's group name. The mapping receives both `group_id` and the original `info` data:

```python
for group in info.get("groups", []):
    if not isinstance(group, dict):
        continue

    # Use the same identifier member names as in the user property mapping.
    candidate_id = group.get("value") or group.get("id")
    if candidate_id != group_id:
        continue

    # Replace these member names with those used by your provider.
    group_name = group.get("display") or group.get("name")
    if group_name:
        return {"name": group_name}

    break

return {"name": str(group_id)}
```

Use the group property mapping only when the identifier is not an appropriate authentik group name.
