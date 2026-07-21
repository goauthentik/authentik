---
title: Token exchange
---

Token exchange allows a client to trade a token it already holds for a new token issued by a different authentik provider. It is defined by [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693), whose abstract states:

> This specification defines a protocol for an HTTP- and JSON-based Security Token Service (STS) by defining how to request and obtain security tokens from OAuth 2.0 authorization servers, including security tokens employing impersonation and delegation.

The typical use is a service that must call another service on behalf of the user who called it. The calling service presents the access token it received as a _subject token_, and receives a token that the second service accepts.

authentik implements _impersonation_: the issued token speaks for the user identified by the subject token, and records no acting party. _Delegation_, in which the issued token names both the user and the service acting on their behalf, is not supported.

### Requirements

The provider performing the exchange must have `Token exchange` selected under **Grant Types**.

The subject token must be verifiable by that provider. Under **Machine-to-Machine authentication settings**, either:

- Add the provider that issued the subject token to **Federated OAuth2/OpenID Providers**, or
- Add the source that issued the subject token to **Federated OIDC Sources**.

A subject token that neither trust relationship covers is rejected. This is the same trust configuration used by the [machine-to-machine](./machine_to_machine.mdx) JWT flow.

Confidential clients must authenticate to the token endpoint. The subject token is not a substitute for client credentials.

### Exchange a token

Send a POST request to the token endpoint:

```http
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange&
client_id=application_client_id&
client_secret=application_client_secret&
subject_token=token_issued_by_the_federated_provider&
subject_token_type=urn:ietf:params:oauth:token-type:access_token&
scope=openid email
```

The response contains the following fields:

- `access_token`: The issued token
- `issued_token_type`: The type identifier of the issued token
- `token_type`: Always `Bearer`
- `expires_in`: The total seconds after which the issued token will expire
- `scope`: The scopes granted to the issued token

The issued token is a new access token for the requesting provider, carrying the identity of the user named by the subject token.

### Supported token types

`subject_token_type` and `requested_token_type` accept:

- `urn:ietf:params:oauth:token-type:access_token`
- `urn:ietf:params:oauth:token-type:jwt`

authentik access tokens are themselves JWTs, so both identifiers refer to the same token. `requested_token_type` is optional and defaults to `urn:ietf:params:oauth:token-type:access_token`.

Any other token type is rejected with `invalid_request`.

### Unsupported parameters

authentik rejects the following rather than ignoring them, so that a client is never led to believe a restriction was applied when it was not:

- `actor_token` and `actor_token_type` are rejected with `invalid_request`, because delegation is not supported.
- `audience` and `resource` are rejected with `invalid_target`, because the issued token cannot be scoped to a named target.

### Scopes

The scopes granted to the issued token are the requested `scope` values, reduced to those the requesting provider is configured to issue. If `scope` is omitted, the issued token is granted no scopes.

### Configure token exchange

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the **Edit** icon on the provider that will perform the exchange.
3. Under **Grant Types**, select `Token exchange`.
4. Expand **Machine-to-Machine authentication settings** and add the issuing provider to **Federated OAuth2/OpenID Providers**.
5. Click **Update**.
