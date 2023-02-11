---
title: Header authentication
---

## Sending authentication

### Send HTTP Basic authentication

Proxy providers have the option to _Send HTTP-Basic Authentication_ to the upstream authentication. When the option in the provider is enabled, two attributes must be specified. These attributes are the keys of values which can be saved on a user or group level that contain the credentials.

For example, with _HTTP-Basic Username Key_ set to `app_username` and _HTTP-Basic Password Key_ set to `app_password`, these attributes would have to be set either on a user or a group the user is member of:

```yaml
app_username: admin
app_password: admin-password
```

These credentials are only retrieved when the user authenticates to the proxy.

If the user does not have a matching attribute, authentik falls back to using the user's email address as username, and the password will be empty if not found.

## Receiving authentication

By default, when _Intercept header authentication_ is enabled, authentik will intercept the authorization header. If the authorization header value is invalid, an error response will be shown with a 401 status code. Requests without an authorization header will still be redirected to the standard login flow.

If the proxied application requires usage of the "Authorization" header, the setting should be disabled. When this setting is disabled, authentik will still attempt to interpret the "Authorization" header, and fall back to the default behaviour if it can't.

### Receiving HTTP Basic authentication

:::info
Requires authentik 2023.1
:::

Proxy providers can receive HTTP basic authentication credentials. The password is expected to be an _App password_, as the credentials are used internally with the [OAuth2 machine-to-machine authentication flow](../oauth2/client_credentials.md).

Access control is done with the policies bound to the application being accessed.

If the received credentials are invalid, a normal authentication flow is initiated. If the credentials are correct, the Authorization header is removed to prevent sending the credentials to the proxied application.

:::danger
It is **strongly** recommended that the client sending requests with HTTP-Basic authentication persists the cookies returned by the outpost. If this is not the case, every request must be authenticated independently, which will increase load on the authentik server and encounter a performance hit.
:::

Starting with authentik 2023.2, logging in with the reserved username `goauthentik.io/token` will behave as if a bearer token was used. All the same options as below apply. This is to allow token-based authentication for applications which might only support basic authentication.

### Receiving HTTP Bearer authentication

:::info
Requires authentik 2023.1
:::

Proxy providers can receive HTTP bearer authentication credentials. The token is expected to be a JWT token issued for the proxy provider. This is described [here](../oauth2/client_credentials.md), using the _client_id_ value shown in the admin interface. Both static and JWT authentication methods are supported.

Access control is done with the policies bound to the application being accessed.

If the received credentials are invalid, a normal authentication flow is initiated. If the credentials are correct, the Authorization header is removed to prevent sending the credentials to the proxied application.

:::caution
It is recommended that the client sending requests with HTTP-Bearer authentication persists the cookies returned by the outpost. For bearer authentication this has a smaller impact than for Basic authentication, but each request is still verified with the authentik server.
:::
