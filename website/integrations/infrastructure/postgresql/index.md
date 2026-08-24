---
title: Integrate with PostgreSQL
sidebar_label: PostgreSQL
support_level: community
---

## What is PostgreSQL?

> PostgreSQL is a powerful, open source object-relational database system with over 35 years of active development.
>
> -- https://www.postgresql.org/

## Preparation

The following placeholders are used in this guide:

- `postgresql.company` is the FQDN of the PostgreSQL server.
- `authentik.company` is the FQDN of the authentik installation.
- `postgresql` is the slug of the authentik application.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

### Requirements

OAuth authentication requires PostgreSQL 18 or later, on both the server and the client. PostgreSQL splits OAuth support into three parts, and each one has to be present:

- **The client** needs the built-in device authorization flow, which lives in the optional `libpq-oauth` module. It is built when PostgreSQL is configured with `--with-libcurl`, and it requires `libcurl` at runtime. Most distributions ship it as a separate package, for example `libpq-oauth` on Debian and Ubuntu. This flow is not available on Windows.
- **The server** needs an OAuth validator module, which checks the bearer token that the client presents and reports which user it belongs to. PostgreSQL does not ship one, so you have to choose and install a third-party module. See [Choosing a validator](#choosing-a-validator) below.
- **authentik** provides the authorization server, through an OAuth2/OpenID Connect provider that has the device code grant enabled.

### Choosing a validator

authentik issues access tokens as JWTs signed with the provider's signing key, so the validator has to fetch the provider's JWKS and verify the signature before trusting any claim in the token. PostgreSQL's [Safely Designing a Validator Module](https://www.postgresql.org/docs/18/oauth-validator-design.html) covers the wider set of concerns.

Several modules exist, and they differ in how much they actually check:

| Module                                                                           | Notes                                                                                                                                                                                                    |
| -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`pg_oidc_validator`](https://github.com/percona/pg_oidc_validator) (Percona)    | Validates JWTs against the provider's JWKS and lets you pick the claim that identifies the user. The most actively maintained of the three. Its authors currently describe the packages as experimental. |
| [`oauth_validator`](https://github.com/TantorLabs/oauth_validator) (Tantor Labs) | Reads `sub` and `scope` straight out of the JWT payload without verifying the signature, so a forged token is accepted. Not suitable unless you add signature verification.                              |
| [`pg_oidc_validator`](https://github.com/dvob/pg_oidc_validator) (dvob)          | Verifies JWTs through OIDC discovery and JWKS, but is published as a proof of concept written to explore Kubernetes service account authentication.                                                      |

This guide uses Percona's module. Whichever you pick, confirm that it verifies token signatures, and review it before using it in production.

## authentik configuration

To support the integration of PostgreSQL with authentik, you need to create an application/provider pair and configure a device code flow in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it is required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** value because it is required later.
        - Set **Client type** to `Public`.
        - Under **Grant Types**, select `Device-code`. PostgreSQL clients use only this grant, so no **Redirect URI** is needed.
        - Select any available signing key. The validator reads the access token as a signed JWT, so a signing key has to be set.
        - Leave **Include claims in id_token** enabled, so that the claims the validator maps users on are carried in the access token.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage access to PostgreSQL and its listing on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Apply a device code flow

PostgreSQL clients use the OAuth device authorization grant, which requires a device code flow on the brand that serves `authentik.company`. This flow is set per brand and is shared by every application that uses this grant, so it is not specific to PostgreSQL. If the brand already has one, skip this section; otherwise follow [Create and apply a device code flow](/docs/add-secure-apps/providers/oauth2/device_code/#create-and-apply-a-device-code-flow).

### Choose the issuer URL

Two separate comparisons have to line up, and both are exact string matches:

- `libpq` builds an issuer identifier from the discovery URL by removing the `/.well-known/` segment, then requires it to equal the `issuer` field inside the discovery document.
- The validator compares the access token's `iss` claim against the `issuer` you set in `pg_hba.conf`.

authentik reports its issuer with a trailing slash, so use that value verbatim in both `pg_hba.conf` and the client connection string:

```text
https://authentik.company/application/o/postgresql/
```

PostgreSQL builds the discovery URL by appending `/.well-known/openid-configuration` to the issuer, which leaves a doubled slash:

```text
https://authentik.company/application/o/postgresql//.well-known/openid-configuration
```

authentik returns `404` for that path, so the reverse proxy in front of authentik has to collapse the doubled slash before passing the request upstream. nginx does not do this by default, because `proxy_pass` without a URI part forwards the original request line unchanged. Routing through `$uri` applies nginx's own path normalization:

```nginx
location / {
    proxy_pass http://authentik$uri$is_args$args;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Confirm the result before configuring PostgreSQL. Both of these have to return the same document, with an `issuer` of `https://authentik.company/application/o/postgresql/`:

```bash
curl -s "https://authentik.company/application/o/postgresql/.well-known/openid-configuration" | jq .issuer
curl -s "https://authentik.company/application/o/postgresql//.well-known/openid-configuration" | jq .issuer
```

:::note Why not the RFC 8414 URL
authentik also serves the same metadata at `https://authentik.company/.well-known/oauth-authorization-server/application/o/postgresql/`, and that URL satisfies `libpq` on its own with no proxy changes. It does not work with `pg_oidc_validator`, which compares the token's `iss` claim against the `issuer` string from `pg_hba.conf` rather than against the issuer identifier derived from it. Setting `issuer` to the RFC 8414 URL makes the validator reject every token with `claim value does not match expected value`. A validator that derives the issuer identifier per RFC 8414, or that takes the expected issuer as its own separate setting, can use that URL and skip the proxy requirement.
:::

## PostgreSQL configuration

### Install and enable the validator

Install `pg_oidc_validator` on the database server, then add it to `postgresql.conf`:

```ini
oauth_validator_libraries = 'pg_oidc_validator'
pg_oidc_validator.authn_field = 'email'
```

`authn_field` selects the claim that identifies the user. It defaults to `sub`, which holds an opaque identifier under authentik's default **Subject Mode**. Setting it to `email` gives a value that maps to database roles more directly. Restart PostgreSQL for `oauth_validator_libraries` to take effect.

### Configure authentication

Add an OAuth entry to `pg_hba.conf`, above any other entry that would match the same connections:

```text
# TYPE     DATABASE  USER  ADDRESS  METHOD  OPTIONS
hostssl    all       all   all      oauth   issuer="https://authentik.company/application/o/postgresql/" scope="openid email" map=authentik
```

The `all` address keyword matches both IPv4 and IPv6 clients. A CIDR such as `0.0.0.0/0` matches IPv4 only, so an IPv6 client would fall through to the next matching entry. The `scope` value has to be covered by the provider's scope mappings in authentik. `openid email` matches the defaults and provides the `email` claim that `authn_field` reads.

Then map identities to database roles in `pg_ident.conf`:

```text
# MAPNAME    SYSTEM-USERNAME         PG-USERNAME
authentik    /^(.*)@company\.com$    \1
```

This maps `alice@company.com` to the `alice` role. Adjust the pattern to your domain and naming, and create the roles in PostgreSQL beforehand. Reload PostgreSQL to apply the `pg_hba.conf` and `pg_ident.conf` changes.

## Configuration verification

To confirm that authentik is properly configured with PostgreSQL, connect with `psql` from a client that has the OAuth flow module available:

```bash
psql "host=postgresql.company dbname=postgres user=alice \
  oauth_issuer=https://authentik.company/application/o/postgresql/ \
  oauth_client_id=<client_id_from_authentik>"
```

`psql` prints a URL and a code:

```text
Visit https://authentik.company/device and enter the code: 284051992
```

Open the URL in a browser, enter the code, and authenticate with authentik. `psql` completes the connection once the flow finishes. Run `SELECT current_user;` and confirm that it returns the mapped role.

Two failures are worth recognizing. A client-side error naming the issuer identifier means the proxy is not collapsing the doubled slash, or the trailing slash is missing from `issuer` or `oauth_issuer`:

```text
failed to fetch OpenID discovery document: unexpected response code 404
```

A server-side rejection in the PostgreSQL log means the token's `iss` claim does not equal the `issuer` string in `pg_hba.conf`:

```text
WARNING:  OAuth validation failed with exception: claim value does not match expected value
FATAL:  OAuth bearer authentication failed for user "alice"
```

If the database server reaches authentik through a different URL than clients do, for example inside a container network, set `pg_oidc_validator.discovery_url_override` to the internal URL. It changes only where the validator fetches metadata and JWKS, not the issuer it expects in the token.

## Resources

- [PostgreSQL documentation - OAuth Authorization/Authentication](https://www.postgresql.org/docs/18/auth-oauth.html)
- [PostgreSQL documentation - OAuth Support in libpq](https://www.postgresql.org/docs/18/libpq-oauth.html)
- [PostgreSQL documentation - OAuth Validator Modules](https://www.postgresql.org/docs/18/oauth-validators.html)
- [pg_oidc_validator repository](https://github.com/percona/pg_oidc_validator)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://datatracker.ietf.org/doc/html/rfc8414)
