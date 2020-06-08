# Expression Policies

!!! notice
    These variables are available in addition to the common variables/functions defined in [**Expressions**](../expressions/index.md)

The passing of the policy is determined by the return value of the code. Use `return True` to pass a policy and `return False` to fail it.

### Available Functions

#### `pb_message(message: str)`

Add a message, visible by the end user. This can be used to show the reason why they were denied.

Example:

```python
pb_message("Access denied")
return False
```

### Context variables

- `request`: A PolicyRequest object, which has the following properties:
    - `request.user`: The current User, which the Policy is applied against. ([ref](../expressions/reference/user-object.md))
    - `request.http_request`: The Django HTTP Request. ([ref](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects))
    - `request.obj`: A Django Model instance. This is only set if the Policy is ran against an object.
    - `request.context`: A dictionary with dynamic data. This depends on the origin of the execution.
- `pb_is_sso_flow`: Boolean which is true if request was initiated by authenticating through an external Provider.
- `pb_client_ip`: Client's IP Address or '255.255.255.255' if no IP Address could be extracted.
- `pb_flow_plan`: Current Plan if Policy is called from the Flow Planner.
