---
title: OAuth2 Provider
---

This provider supports both generic OAuth2 as well as OpenID Connect

Scopes can be configured using Scope Mappings, a type of [Property Mappings](../../property-mappings/#scope-mapping).

| Endpoint             | URL                                                                  |
| -------------------- | -------------------------------------------------------------------- |
| Authorization        | `/application/o/authorize/`                                          |
| Token                | `/application/o/token/`                                              |
| User Info            | `/application/o/userinfo/`                                           |
| Token Revoke         | `/application/o/revoke/`                                             |
| End Session          | `/application/o/<application slug>/end-session/`                     |
| JWKS                 | `/application/o/<application slug>/jwks/`                            |
| OpenID Configuration | `/application/o/<application slug>/.well-known/openid-configuration` |

## GitHub Compatibility

This provider also exposes a GitHub-compatible endpoint. This endpoint can be used by applications, which support authenticating against GitHub Enterprise, but not generic OpenID Connect.

To use any of the GitHub Compatibility scopes, you have to use the GitHub Compatibility Endpoints.

| Endpoint        | URL                         |
| --------------- | --------------------------- |
| Authorization   | `/login/oauth/authorize`    |
| Token           | `/login/oauth/access_token` |
| User Info       | `/user`                     |
| User Teams Info | `/user/teams`               |

To access the user's email address, a scope of `user:email` is required. To access their groups, `read:org` is required. Because these scopes are handled by a different endpoint, they are not customisable as a Scope Mapping.

## Grant types

### `authorization_code`:

This grant is used to convert an authorization code to a refresh token. The authorization code is retrieved through the Authorization flow, and can only be used once, and expires quickly.

### `refresh_token`:

Refresh tokens can be used as long-lived tokens to access user data, and further renew the refresh token down the road.

### `client_credentials`:

See [Machine-to-machine authentication](./client_credentials)

## Scope authorization

By default, every user that has access to an application can request any of the configured scopes. Starting with authentik 2022.4, you can do additional checks for the scope in an expression policy (bound to the application):

```python
# There are additional fields set in the context, use `ak_logger.debug(request.context)` to see them.
if "my-admin-scope" in request.context["oauth_scopes"]:
    return ak_is_group_member(request.user, name="my-admin-group")
return True
```

## Special scopes

#### GitHub compatibility

-   `user`: No-op, is accepted for compatibility but does not give access to any resources
-   `read:user`: Same as above
-   `user:email`: Allows read-only access to `/user`, including email address
-   `read:org`: Allows read-only access to `/user/teams`, listing all the user's groups as teams.

#### authentik

-   `goauthentik.io/api`: This scope grants the refresh token access to the authentik API on behalf of the user

## Default scopes

:::info
Requires authentik 2022.7
:::

When a client does not request any scopes, authentik will treat the request as if all configured scopes were requested. Depending on the configured authorization flow, consent still needs to be given, and all scopes are listed there.

This does _not_ apply to special scopes, as those are not configurable in the provider.
