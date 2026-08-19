---
title: Token exchange
sidebar_position: 2
---

Token exchange allows a client to exchange a token it already holds for a new token issued by an authentik provider. Token exchange is defined by [RFC 8693](https://datatracker.ietf.org/doc/html/rfc8693), whose abstract states:

> This specification defines a protocol for an HTTP- and JSON-based Security Token Service (STS) by defining how to request and obtain security tokens from OAuth 2.0 authorization servers, including security tokens employing impersonation and delegation.

A typical use case involves a service calling another service on behalf of a user. The calling service presents the user's access token as a _subject token_ and receives a new token that the other service accepts.

authentik supports both token exchange modes defined by RFC 8693:

- **Impersonation**: When the request contains only a subject token, the issued token identifies the user represented by that token and does not record an acting party.
- **Delegation**, also known as on-behalf-of (OBO) token exchange :ak-version[2026.8]: When the request also contains an actor token, the issued token identifies the user as its subject and records the authentik Actor that represents the acting party.

## Requirements

The provider performing the exchange must:

- Have `Token exchange` selected under **Grant Types**.
- Be bound to an application.

The provider performing the exchange must be able to verify the subject token. Under **Machine-to-Machine authentication settings**, configure one of the following trust relationships:

- Add the provider that issued the subject token to **Federated OAuth2/OpenID Providers**.
- Add the source that issued the subject token to **Federated OIDC Sources**.

Normally, authentik rejects a subject token that cannot be verified through either trust relationship. When `audience` targets a different provider, authentik also accepts a subject token issued by the provider performing the exchange. The target provider must explicitly trust the provider performing the exchange, as described in [Audience](#audience).

These trust relationships are also used by the [machine-to-machine](./machine_to_machine.mdx) JWT flow.

Confidential clients must authenticate to the token endpoint. The subject token does not replace the client's credentials.

For delegation, the actor token must identify an authentik Actor. Ordinary users and non-Actor service accounts cannot be used as actors. OBO does not require a separate provider setting. Enabling the `Token exchange` grant also enables delegation.

authentik resolves actor tokens presented as OAuth access tokens or JWTs through **Federated OAuth2/OpenID Providers**. When `audience` targets a different provider, authentik also accepts an actor token issued by the provider performing the exchange. Unlike subject tokens, actor tokens cannot be resolved through **Federated OIDC Sources**.

## Exchange a token

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

- `access_token`: The issued access token
- `issued_token_type`: The type identifier of the issued token
- `token_type`: The token type, which is always `Bearer`
- `expires_in`: The number of seconds until the issued token expires
- `scope`: The scopes granted to the issued token

The resulting access token carries the identity of the user identified by the subject token. By default, authentik creates the token using the provider performing the exchange. If [`audience`](#audience) identifies a different provider, authentik uses the target provider's configuration instead.

## Exchange a token on behalf of a user (OBO)

To perform a delegation exchange, include `actor_token` and `actor_token_type` in addition to `subject_token` and `subject_token_type`.

The subject token, supplied using `subject_token`, identifies the user on whose behalf the request is made. The actor token, supplied using `actor_token`, identifies the authentik Actor performing the action.

```http
POST /application/o/token/ HTTP/1.1
Host: authentik.company
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange&
client_id=application_client_id&
client_secret=application_client_secret&
subject_token=token_identifying_the_user&
subject_token_type=urn:ietf:params:oauth:token-type:access_token&
actor_token=authentik_api_token_for_the_actor&
actor_token_type=goauthentik.io/oauth/token-type/authentik_token&
scope=openid email
```

`actor_token` and `actor_token_type` must be included together or omitted together. If both parameters are omitted, authentik performs an impersonation exchange.

The following requirements apply to an OBO exchange:

- The user identified by `subject_token` remains the subject of the issued token.
- The actor must be an authentik Actor. Ordinary users and non-Actor service accounts cannot be used as actors.
- If the Actor has a parent user, that parent must be the user identified by `subject_token`.
- An Actor without a parent can be used only when `actor_token` is an OAuth access token or JWT. An Actor without a parent cannot authenticate using an authentik API token.

The issued JWT contains the RFC 8693 `act` claim, which identifies the Actor:

```json
{
    "sub": "subject_identifier",
    "act": {
        "sub": "actor_identifier"
    }
}
```

The provider used to issue the token determines the identifiers for `sub` and `act.sub` according to its **Subject mode**. When `audience` selects another provider, the target provider's subject mode is used.

## Supported token types

### Subject and requested token types

`subject_token_type` and `requested_token_type` accept the following values:

- `urn:ietf:params:oauth:token-type:access_token`
- `urn:ietf:params:oauth:token-type:jwt`

Because authentik access tokens are JWTs, authentik treats both token-type values equivalently. `requested_token_type` is optional and defaults to `urn:ietf:params:oauth:token-type:access_token`.

For any other subject or requested token type, authentik rejects the request with `invalid_request`.

### Actor token types

`actor_token_type` accepts the following values:

- `urn:ietf:params:oauth:token-type:access_token`
- `urn:ietf:params:oauth:token-type:jwt`
- `goauthentik.io/oauth/token-type/authentik_token`

Because authentik OAuth access tokens are JWTs, authentik treats the first two token-type values equivalently.

Both values indicate that `actor_token` contains an authentik OAuth access token issued to an Actor. The token must correspond to an authentik access-token record and must have been issued by an eligible authentik provider. Normally, the issuing provider must be listed under **Federated OAuth2/OpenID Providers** in the configuration of the provider performing the exchange. When `audience` targets a different provider, the provider performing the exchange is also eligible. authentik does not use federated OIDC sources to resolve actor tokens.

`goauthentik.io/oauth/token-type/authentik_token` is an authentik-specific token type for a built-in authentik API token. The API token must belong to an Actor whose parent is the user identified by the subject token.

If either `actor_token` or `actor_token_type` is supplied without the other, authentik rejects the request with `invalid_request`. authentik also rejects unsupported actor token types with `invalid_request`.

If both parameters are present but the actor token is unknown, expired, or cannot be verified, authentik rejects the request with `invalid_grant`. authentik also returns `invalid_grant` if the token does not belong to an Actor or if the Actor has a parent other than the user identified by the subject token.

## Audience

By default, authentik creates the new token using the provider performing the exchange. Set `audience` to request a token using a different provider's configuration:

```http
audience=target_application_client_id
```

The value must be the target provider's `client_id` or the `pbm_uuid` of the application to which the target provider is bound. authentik accepts only one `audience` value and does not support tokens for multiple providers.

The resulting token uses the target provider's configuration. authentik signs the token using the target provider's signing key. The token uses the target provider's issuer as `iss` and its `client_id` as `aud`. The target provider's subject mode and scope mappings also apply. The target provider's endpoints, including its userinfo, introspection, and revocation endpoints, accept the token.

For an OBO exchange, the target provider's subject mode determines both the user identifier in `sub` and the Actor identifier in `act.sub`.

When `audience` identifies a provider other than the provider performing the exchange, both of the following conditions must be met; otherwise, authentik rejects the request with `invalid_target`:

- The target provider must list the provider performing the exchange under **Federated OAuth2/OpenID Providers**. This trust relationship explicitly permits the provider performing the exchange to mint tokens for the target provider.
- The target provider must be bound to an application.

The user identified by the subject token must also pass the target application's policy bindings; otherwise, authentik rejects the request with `invalid_grant`.

## Unsupported parameters

authentik rejects requests containing `resource` with `invalid_target` rather than ignoring the parameter. This prevents clients from incorrectly assuming that authentik applied the requested restriction. Use `audience` to identify the target provider instead.

## Scopes

The issued token includes only requested scopes with corresponding scope mappings assigned to the provider used to issue it. When `audience` identifies a target provider, authentik uses the target provider's scope mappings. Otherwise, it uses those of the provider performing the exchange.

If `scope` is omitted, the issued token has no scopes.

## Configure token exchange

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the **Edit** icon for the provider that will perform the exchange.
3. Under **Grant Types**, select `Token exchange`.
4. Expand **Machine-to-Machine authentication settings**.
5. Configure the trust relationships required to verify subject tokens:
    - Add authentik providers that issue subject tokens to **Federated OAuth2/OpenID Providers**.
    - Alternatively, add external OIDC sources that issue subject tokens to **Federated OIDC Sources**.
6. To use an OAuth access token or JWT as `actor_token`, add the provider that issued the token to **Federated OAuth2/OpenID Providers**. When `audience` targets a different provider, an actor token issued by the provider performing the exchange is also accepted.
7. Click **Update**.
8. To target another provider using `audience`, edit the target provider and add the provider performing the exchange to the target provider's **Federated OAuth2/OpenID Providers**.
9. To perform an OBO exchange, obtain a token issued to the Actor that will act on the user's behalf. Supply the token using `actor_token` and set the corresponding `actor_token_type`.
