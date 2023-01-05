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

### `list_flatten(value: list[Any] | Any) -> Optional[Any]`

Flatten a list by either returning its first element, None if the list is empty, or the passed in object if its not a list.

Example:

```python
user = list_flatten(["foo"])
# user = "foo"
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

### `ak_user_has_authenticator(user: User, device_type: Optional[str] = None) -> bool` (2021.9+)

:::info
Only available in property mappings with authentik 2022.9 and newer
:::

Check if a user has any authenticator devices. Only fully validated devices are counted.

Optionally, you can filter a specific device type. The following options are valid:

-   `totp`
-   `duo`
-   `static`
-   `webauthn`

Example:

```python
return ak_user_has_authenticator(request.user)
```

### `ak_create_event(action: str, **kwargs) -> None`

:::info
Requires authentik 2022.9
:::

Create a new event with the action set to `action`. Any additional key-word parameters will be saved in the event context. Additionally, `context` will be set to the context in which this function is called.

Before saving, any data-structure which are not representable in JSON are flattened, and credentials are removed.

The event is saved automatically

Example:

```python
ak_create_event("my_custom_event", foo=request.user)
```

## Comparing IP Addresses

To compare IP Addresses or check if an IP Address is within a given subnet, you can use the functions `ip_address('192.0.2.1')` and `ip_network('192.0.2.0/24')`. With these objects you can do [arithmetic operations](https://docs.python.org/3/library/ipaddress.html#operators).

You can also check if an IP Address is within a subnet by writing the following:

```python
ip_address('192.0.2.1') in ip_network('192.0.2.0/24')
# evaluates to True
```
