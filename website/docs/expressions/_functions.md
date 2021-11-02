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

### `ak_is_group_member(user: User, **group_filters) -> bool`

Check if `user` is member of a group matching `**group_filters`.

Example:

```python
return ak_is_group_member(request.user, name="test_group")
```

### `ak_user_by(**filters) -> Optional[User]`

Fetch a user matching `**filters`.

Returns "None" if no user was found, otherwise [User](/docs/user-group/user)

Example:

```python
other_user = ak_user_by(username="other_user")
```

## Comparing IP Addresses

To compare IP Addresses or check if an IP Address is within a given subnet, you can use the functions `ip_address('192.0.2.1')` and `ip_network('192.0.2.0/24')`. With these objects you can do [arithmetic operations](https://docs.python.org/3/library/ipaddress.html#operators).

You can also check if an IP Address is within a subnet by writing the following:

```python
ip_address('192.0.2.1') in ip_network('192.0.2.0/24')
# evaluates to True
```
