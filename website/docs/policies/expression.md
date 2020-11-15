---
title: Expression Policies
---

:::note
These variables are available in addition to the common variables/functions defined in [**Expressions**](../expressions/index.md)
:::

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

-   `request`: A PolicyRequest object, which has the following properties:
    -   `request.user`: The current user, against which the policy is applied. ([ref](../expressions/reference/user-object.md))
    -   `request.http_request`: The Django HTTP Request. ([ref](https://docs.djangoproject.com/en/3.0/ref/request-response/#httprequest-objects))
    -   `request.obj`: A Django Model instance. This is only set if the policy is ran against an object.
    -   `request.context`: A dictionary with dynamic data. This depends on the origin of the execution.
-   `pb_is_sso_flow`: Boolean which is true if request was initiated by authenticating through an external provider.
-   `pb_client_ip`: Client's IP Address or 255.255.255.255 if no IP Address could be extracted. Can be [compared](../expressions/index.md#comparing-ip-addresses), for example

    ```python
    return pb_client_ip in ip_network('10.0.0.0/24')
    ```

Additionally, when the policy is executed from a flow, every variable from the flow's current context is accessible under the `context` object.

This includes the following:

-   `prompt_data`: Data which has been saved from a prompt stage or an external source.
-   `application`: The application the user is in the process of authorizing.
-   `pending_user`: The currently pending user
