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

### `ak_call_policy(name: str, **kwargs) -> PolicyResult`

:::info
Requires authentik 2021.12
:::

Call another policy with the name _name_. Current request is passed to policy. Key-word arguments
can be used to modify the request's context.

Example:

```python
result = ak_call_policy("test-policy")
# result is a PolicyResult object, so you can access `.passing` and `.messages`.
# Starting with authentik 2023.4 you can also access `.raw_result`, which is the raw value returned from the called policy
# `result.passing` will always be a boolean if the policy is passing or not.
return result.passing

result = ak_call_policy("test-policy-2", foo="bar")
# Inside the `test-policy-2` you can then use `request.context["foo"]`
return result.passing
```

### `ak_is_group_member(user: User, **group_filters) -> bool`

Check if `user` is member of a group matching `**group_filters`.

Example:

```python
return ak_is_group_member(request.user, name="test_group")
```

### `ak_user_by(**filters) -> Optional[User]`

Fetch a user matching `**filters`.

Returns "None" if no user was found, otherwise returns the [User](/docs/user-group/user) object.

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

## DNS resolution and reverse DNS lookups

:::note
Requires authentik 2023.3 or higher
:::

To resolve a hostname to a list of IP addresses, use the functions `resolve_dns(hostname)` and `resolve_dns(hostname, ip_version)`.

```python
resolve_dns("google.com")  # return a list of all IPv4 and IPv6 addresses
resolve_dns("google.com", 4)  # return a list of only IP4 addresses
resolve_dns("google.com", 6)  # return a list of only IP6 addresses
```

You can also do reverse DNS lookups.

:::note
Reverse DNS lookups may not return the expected host if the IP address is part of a shared hosting environment.
See: https://stackoverflow.com/a/19867936
:::

To perform a reverse DNS lookup use `reverse_dns("192.0.2.0")`. If no DNS records are found the original IP address is returned.

:::info
DNS resolving results are cached in memory. The last 32 unique queries are cached for up to 3 minutes.
:::
