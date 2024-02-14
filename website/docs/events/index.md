---
title: Events
---

Events are authentik's built-in logging system. Whenever any of the following actions occur, an event is created:

Certain information is stripped from events, to ensure no passwords or other credentials are saved in the log.

## Event retention

The event retention is configured in the system settings interface, with the default being set to 365 days.

If you want to forward these events to another application, forward the log output of all authentik containers. Every event creation is logged with the log level "info". For this configuration, it is also recommended to set the internal retention pretty low (for example, `days=1`).

## Event actions

### `login`

A user logs in (including the source, if available)

<details>
<summary>Example</summary>

```json
{
    "pk": "f00f54e7-2b38-421f-bc78-e61f950048d6",
    "user": {
        "pk": 1,
        "email": "root@localhost",
        "username": "akadmin"
    },
    "action": "login",
    "app": "authentik.events.signals",
    "context": {
        "auth_method": "password",
        "http_request": {
            "args": {
                "query": "next=%2F"
            },
            "path": "/api/v3/flows/executor/default-authentication-flow/",
            "method": "GET"
        },
        "auth_method_args": {}
    },
    "client_ip": "::1",
    "created": "2023-02-15T15:33:42.771091Z",
    "expires": "2024-02-15T15:33:42.770425Z",
    "brand": {
        "pk": "fcba828076b94dedb2d5a6b4c5556fa1",
        "app": "authentik_brands",
        "name": "Default brand",
        "model_name": "brand"
    }
}
```

</details>

### `login_failed`

A failed login attempt

<details>
<summary>Example</summary>

```json
{
    "pk": "2779b173-eb2a-4c2b-a1a4-8283eda308d7",
    "user": {
        "pk": 2,
        "email": "",
        "username": "AnonymousUser"
    },
    "action": "login_failed",
    "app": "authentik.events.signals",
    "context": {
        "stage": {
            "pk": "7e88f4a991c442c1a1335d80f0827d7f",
            "app": "authentik_stages_password",
            "name": "default-authentication-password",
            "model_name": "passwordstage"
        },
        "password": "********************",
        "username": "akadmin",
        "http_request": {
            "args": {
                "query": "next=%2F"
            },
            "path": "/api/v3/flows/executor/default-authentication-flow/",
            "method": "POST"
        }
    },
    "client_ip": "::1",
    "created": "2023-02-15T15:32:55.319608Z",
    "expires": "2024-02-15T15:32:55.314581Z",
    "brand": {
        "pk": "fcba828076b94dedb2d5a6b4c5556fa1",
        "app": "authentik_brands",
        "name": "Default brand",
        "model_name": "brand"
    }
}
```

</details>

### `logout`

A user logs out.

<details>
<summary>Example</summary>

```json
{
    "pk": "474ffb6b-77e3-401c-b681-7d618962440f",
    "user": {
        "pk": 1,
        "email": "root@localhost",
        "username": "akadmin"
    },
    "action": "logout",
    "app": "authentik.events.signals",
    "context": {
        "http_request": {
            "args": {
                "query": ""
            },
            "path": "/api/v3/flows/executor/default-invalidation-flow/",
            "method": "GET"
        }
    },
    "client_ip": "::1",
    "created": "2023-02-15T15:39:55.976243Z",
    "expires": "2024-02-15T15:39:55.975535Z",
    "brand": {
        "pk": "fcba828076b94dedb2d5a6b4c5556fa1",
        "app": "authentik_brands",
        "name": "Default brand",
        "model_name": "brand"
    }
}
```

</details>

### `user_write`

A user is written to during a flow execution.

<details>
<summary>Example</summary>

```json
{
    "pk": "d012e8af-cb94-4fa2-9e92-961e4eebc060",
    "user": {
        "pk": 1,
        "email": "root@localhost",
        "username": "akadmin"
    },
    "action": "user_write",
    "app": "authentik.events.signals",
    "context": {
        "name": "authentik Default Admin",
        "email": "root@localhost",
        "created": false,
        "username": "akadmin",
        "attributes": {
            "settings": {
                "locale": ""
            }
        },
        "http_request": {
            "args": {
                "query": ""
            },
            "path": "/api/v3/flows/executor/default-user-settings-flow/",
            "method": "GET"
        }
    },
    "client_ip": "::1",
    "created": "2023-02-15T15:41:18.411017Z",
    "expires": "2024-02-15T15:41:18.410276Z",
    "brand": {
        "pk": "fcba828076b94dedb2d5a6b4c5556fa1",
        "app": "authentik_brands",
        "name": "Default brand",
        "model_name": "brand"
    }
}
```

</details>

### `suspicious_request`

A suspicious request has been received (for example, a revoked token was used).

### `password_set`

A user sets their password.

### `secret_view`

A user views a token's/certificate's data.

### `secret_rotate`

A token was rotated automatically by authentik.

### `invitation_used`

An invitation is used.

### `authorize_application`

A user authorizes an application.

<details>
<summary>Example</summary>

```json
{
    "pk": "f52f9eb9-dc2a-4f1e-afea-ad5af90bf680",
    "user": {
        "pk": 1,
        "email": "root@localhost",
        "username": "akadmin"
    },
    "action": "authorize_application",
    "app": "authentik.providers.oauth2.views.authorize",
    "context": {
        "asn": {
            "asn": 6805,
            "as_org": "Telefonica Germany",
            "network": "5.4.0.0/14"
        },
        "geo": {
            "lat": 42.0,
            "city": "placeholder",
            "long": 42.0,
            "country": "placeholder",
            "continent": "placeholder"
        },
        "flow": "53287faa8a644b6cb124cb602a84282f",
        "scopes": "ak_proxy profile openid email",
        "http_request": {
            "args": {
                "query": "[...]"
            },
            "path": "/api/v3/flows/executor/default-provider-authorization-implicit-consent/",
            "method": "GET"
        },
        "authorized_application": {
            "pk": "bed6a2495fdc4b2e8c3f93cb2ed7e021",
            "app": "authentik_core",
            "name": "Alertmanager",
            "model_name": "application"
        }
    },
    "client_ip": "::1",
    "created": "2023-02-15T10:02:48.615499Z",
    "expires": "2023-04-26T10:02:48.612809Z",
    "brand": {
        "pk": "10800be643d44842ab9d97cb5f898ce9",
        "app": "authentik_brands",
        "name": "Default brand",
        "model_name": "brand"
    }
}
```

</details>

### `source_linked`

A user links a source to their account

### `impersonation_started` / `impersonation_ended`

A user starts/ends impersonation, including the user that was impersonated

### `policy_execution`

A policy is executed (when a policy has "Execution Logging" enabled).

### `policy_exception` / `property_mapping_exception`

A policy or property mapping causes an exception

### `system_task_exception`

An exception occurred in a system task.

### `system_exception`

A general exception in authentik occurred.

### `configuration_error`

A configuration error occurs, for example during the authorization of an application

### `model_created` / `model_updated` / `model_deleted`

Logged when any model is created/updated/deleted, including the user that sent the request.

:::info
Starting with authentik 2024.2, when a valid enterprise license is installed, these entries will contain additional audit data, including which fields were changed with this event, their previous values and their new values.
:::

### `email_sent`

An email has been sent. Included is the email that was sent.

### `update_available`

An update is available
