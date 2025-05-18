---
title: Source property mappings
---

Source property mappings allow you to modify or gather extra information from sources.

This page is an overview of how property mappings work. For information about specific protocol, please refer to each protocol page:

- [Kerberos](../protocols/kerberos/#kerberos-source-property-mappings)
- [LDAP](../protocols/ldap/index.md#ldap-source-property-mappings)
- [OAuth](../protocols/oauth/index.mdx#oauth-source-property-mappings)
- [SAML](../protocols/saml/index.md#saml-source-property-mappings)
- [SCIM](../protocols/scim/index.md#scim-source-property-mappings)

## Create a custom source property mapping

If the default source mappings are not enough, or if you need to get additional data from the source, you can create your own custom source property mappings.

Here are the steps:

1. In authentik, open the Admin interface, and then navigate to **Customization -> Property Mappings**.
2. Click **Create**, select the property mapping type for your source, and then click **Next**.
3. Type a unique and meaningful **Name**, such as `ldap-displayName-mapping:name`.
4. In the **Expression** field enter Python expressions to retrieve the value from the source. See [Expression Semantics](#expression-semantics) below for details.
5. In the source configuration, select the newly created property mapping as a **User property mapping** if it applies to users, or **Group property mapping** if it applies to groups.

## How it works

### Expression semantics

Each source provides the Python expression with additional data. You can import parts of that data into authentik users and groups. Assuming the source provides us with a `data` Python dictionary, you can write the following:

```python
return {
    "name": data.get("displayName"),
}
```

You can see that the expression returns a Python dictionary. The dictionary keys must match [User properties](../../user/user_ref.mdx#object-properties) or [Group properties](../../groups/group_ref.md#object-properties). Note that for users, `ak_groups` and `group_attributes` cannot be set.

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
    - If a property mapping throws an error, the process is aborted. If that happens inside a synchronization process, the object is skipped. If it happens during an enrollment or authentication flow, the flow is cancelled.
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

The `groups` attribute is a special attribute that must contain group identifiers. By default, those identifiers are also used as the group name by default, those identifiers are also used as the group name. Each of those identifiers is then given to group property mappings as the `group_id` variable, if extra processing needs to happen.
