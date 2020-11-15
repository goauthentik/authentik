---
title: Expressions
---

Expressions allow you to write custom logic using Python code.

Expressions are used in different places throughout passbook, and can do different things.

:::info
These functions/objects are available wherever expressions are used. For more specific information, see [Expression Policies](../policies/expression.md) and [Property Mappings](../property-mappings/expression.md)
:::

## Global objects

-   `pb_logger`: structlog BoundLogger. ([ref](https://www.structlog.org/en/stable/api.html#structlog.BoundLogger))
-   `requests`: requests Session object. ([ref](https://requests.readthedocs.io/en/master/user/advanced/))

## Generally available functions

### `regex_match(value: Any, regex: str) -> bool`

Check if `value` matches Regular Expression `regex`.

Example:

```python
return regex_match(request.user.username, '.*admin.*')
```

### `regex_replace(value: Any, regex: str, repl: str) -> str`

Replace anything matching `regex` within `value` with `repl` and return it.

Example:

```python
user_email_local = regex_replace(request.user.email, '(.+)@.+', '')
```

### `pb_is_group_member(user: User, **group_filters) -> bool`

Check if `user` is member of a group matching `**group_filters`.

Example:

```python
return pb_is_group_member(request.user, name="test_group")
```

### `pb_user_by(**filters) -> Optional[User]`

Fetch a user matching `**filters`. Returns "None" if no user was found.

Example:

```python
other_user = pb_user_by(username="other_user")
```

## Comparing IP Addresses

To compare IP Addresses or check if an IP Address is within a given subnet, you can use the functions `ip_address('192.0.2.1')` and `ip_network('192.0.2.0/24')`. With these objects you can do [arithmetic operations](https://docs.python.org/3/library/ipaddress.html#operators).

You can also check if an IP Address is within a subnet by writing the following:

```python
ip_address('192.0.2.1') in ip_network('192.0.2.0/24')
# evaluates to True
```
