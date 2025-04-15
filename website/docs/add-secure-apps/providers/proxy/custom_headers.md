---
title: Custom headers
---

The proxy can send custom headers to your upstream application. These can be configured in one of two ways:

- Group attributes; this allows for inheritance, but only allows static values
- Property mappings; this allows for dynamic values

## Group attributes

Edit the group or user you wish the header to be set for, and set these attributes:

```yaml
additionalHeaders:
    X-My-Header: value
```

You can the add users to this group or override the field in users.

## Property Mappings

For dynamic Header values (for example, your application requires X-App-User to contain the username), property mappings can be used.

Create a new Scope mapping with a name and scope of your choice, and use an expression like this:

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

After you've created this Scope mapping, make sure to edit the proxy provider and select the mapping.

As you can see by the similar structure, this just overrides any static attributes, so both of these methods can be combined.
