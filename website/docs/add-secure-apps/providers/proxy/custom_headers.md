---
title: Custom headers
---

The proxy can send custom headers to your upstream application. Configure these headers in one of two ways:

- Group or user attributes, which allow static values.
- Property mappings, which allow dynamic values.

## Group or user attributes

Edit the group or user that should set the header, and set the following attributes:

```yaml
additionalHeaders:
    X-My-Header: value
```

You can then add users to the group or override the field on individual users.

## Property mappings

Use property mappings for dynamic header values, for example when an application requires `X-App-User` to contain the username.

Create a new scope mapping with a name and scope of your choice, and use an expression like this:

```python
return {
    "ak_proxy": {
        "user_attributes": {
            "additionalHeaders": {
                "X-App-User": request.user.username
            }
        }
    }
}
```

After you create this scope mapping, edit the proxy provider and select the mapping under **Additional scopes**.

The property mapping uses the same `additionalHeaders` structure as group and user attributes, so both methods can be combined. When both methods set the same header, the property mapping value overrides the static attribute value.
