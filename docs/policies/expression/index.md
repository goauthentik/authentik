# Expression Policy

Expression Policies allows you to write custom Policy Logic using Python code..

The passing of the policy is determined by the return value of the code. Use `return True` to pass a policy and `return False` to fail it.

## Available objects

#### When invoked from a PolicyRequest (most cases)

- `request`: A PolicyRequest object, which has the following properties:
    - `request.user`: The current User, which the Policy is applied against. ([ref](../../property-mappings/reference/user-object.md))
    - `request.http_request`: The Django HTTP Request, as documented [here](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects).
    - `request.obj`: A Django Model instance. This is only set if the Policy is ran against an object.
    - `request.context`: A dictionary with dynamic data. This depends on the origin of the execution.
- `pb_is_sso_flow`: Boolean which is true if request was initiated by authenticating through an external Provider.

#### When invoked from an HTTPRequest

- `pb_client_ip`: Client's IP Address or '255.255.255.255' if no IP Address could be extracted.
- `pb_flow_plan`: Current Plan if Policy is called from the Flow Planner.

## Available Functions

#### `regex_match(value: Any, regex: str) -> bool`

Check if `value` matches Regular Expression `regex`.

Example:

```python
return regex_match(request.user.username, '.*admin.*')
```

#### `regex_replace(value: Any, regex: str, repl: str) -> str`

Replace anything matching `regex` within `value` with `repl` and return it.

Example:

```python
user_email_local = regex_replace(request.user.email, '(.+)@.+', '')
```

#### `pb_message(message: str)`

Add a message, visible by the end user. This can be used to show the reason why they were denied.

Example:

```python
pb_message("Access denied")
```

#### `pb_is_group_member(user: User, **group_filters) -> bool`

Check if `user` is member of a group matching `**group_filters`.

Example:

```python
return pb_is_group_member(request.user, name="test_group")
```

#### `pb_user_by(**filters) -> Optional[User]`

Fetch a user matching `**filters`. Returns None if no user was found.

Example:

```python
other_user = pb_user_by(username="other_user")
```

#### Special objects

- `pb_logger`: structlog BoundLogger, see [API Reference](https://www.structlog.org/en/stable/api.html#structlog.BoundLogger)
- `requests`: requests Session object, see [API Reference](https://requests.readthedocs.io/en/master/user/advanced/)
