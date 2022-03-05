---
title: OAuth2 Provider
---

This provider supports both generic OAuth2 as well as OpenID Connect

Scopes can be configured using Scope Mappings, a type of [Property Mappings](../property-mappings/#scope-mapping).

| Endpoint             | URL                                                                  |
| -------------------- | -------------------------------------------------------------------- |
| Authorization        | `/application/o/authorize/`                                          |
| Token                | `/application/o/token/`                                              |
| User Info            | `/application/o/userinfo/`                                           |
| End Session          | `/application/o/end-session/`                                        |
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

Client credentials can be used for machine-to-machine communication authentication. Clients can authenticate themselves using service-accounts; standard client_id + client_secret is not sufficient. This behavior is due to providers only being able to have a single secret at any given time.

Hence identification is based on service-accounts, and authentication is based on App-password tokens. These objects can be created in a single step using the *Create Service account* function.

An example request can look like this:

```
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&username=my-service-account&password=my-token
```

This will return a JSON response with an `access_token`, which is a signed JWT token. This token can be sent along requests to other hosts, which can then validate the JWT based on the signing key configured in authentik.
