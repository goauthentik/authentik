# MCP conformance: authentik as ID-JAG Resource Authorization Server

GitHub check: **`test-mcp-conformance (id-jag-resource-as)`**, a second matrix row in `.github/workflows/ci-mcp-id_jag_issuer.yml`.

This suite is the other half of `tests/mcp_conformance_id_jag_issuer/`. There, authentik issues an Identity Assertion JWT Authorization Grant (ID-JAG) and an independent fixture redeems it. Here, authentik **redeems** ID-JAGs: a client presents one at authentik's token endpoint with the RFC 7523 jwt-bearer grant, and authentik returns an access token (draft-ietf-oauth-identity-assertion-authz-grant-06 §4.4).

## What runs

```
stub IdP (selfcheck_resource_as.StubIdP)   authentik (live server)
----------------------------------------   -----------------------
RFC 8414 metadata + JWKS  <--------------- admin API: OIDC source from the IdP metadata URL
signs ID-JAGs (cryptography, own code)     provider: jwt-bearer grant + that source as trusted
            |                              user connected to the IdP subject
            +---- POST /token jwt-bearer + Basic ----> access token
                                           verified with the independent JOSE verifier
                                           (resource_as.py) against authentik's JWKS; userinfo
```

* **IdP Authorization Server**: the issuer suite's `StubIdP`. It serves RFC 8414 metadata and JWKS, and signs with `cryptography` directly, so authentik validates assertions it did not produce.
* **Trust** is configured the way an administrator would: an OpenID Connect source is created through the API from the IdP's metadata URL (authentik fetches the JWKS), and the provider lists it in `jwt_federation_sources`. authentik binds the ID-JAG `iss` to the issuer that metadata URL is derived from, so keys trusted for one issuer don't validate assertions naming another.
* **Subject**: `iss` + `sub` is the stable identifier: the ID-JAG `sub` matches an existing connection between a user and that source, as an earlier SSO through the IdP would create. Without one, the `email` claim can find a user who already exists, as the MCP enterprise-managed authorization extension describes and as Claude-issued ID-JAGs (whose `sub` is opaque) require. That only happens in the email domains an administrator lists on the source (**ID-JAG email domains**), because an issuer can assert any address (§9.8). The match ignores case, must name exactly one active, non-service-account user who isn't already connected to that source, and is refused if `email_verified` is present and not `true`. The user is connected to the subject once the application's policies allow them, so later ID-JAGs resolve by `sub`. Otherwise authentik answers `access_denied` (§4.4.3); users aren't created on first use.
* **authentik to authentik**: `ras.e2e.authentik-issuer` has authentik issue an ID-JAG through token exchange (the issuance work from goauthentik/authentik#26973) and redeem it as a Resource AS.

## Checks

`catalog.py` lists 22 check IDs; the run passes only if each runs once and passes. Negatives are gated on the `ras.redeem` positive control. The report format, statuses and gating are shared with the issuer suite (`checks.Report`).

**Expected red:** `ras.resource-bound`. §4.4.1 requires each `resource` in an ID-JAG to be a protected resource the Resource AS governs, and the access token to be restricted to it. Providers can't declare governed resources until RFC 8707 support lands (the `oauth2/resource-indicators` work adds `OAuth2Provider.allowed_resources`), so authentik refuses resource-bound ID-JAGs with `invalid_grant`. That keeps it spec-correct, but an MCP flow, where the ID-JAG names the MCP server, can't complete yet.

## Not implemented yet

| Rule | Status |
| --- | --- |
| Governed `resource`, audience-restricted access token (§4.4.1, RFC 8707) | refused (`invalid_grant`); `ras.resource-bound` is red |
| Sender-constrained ID-JAGs, `cnf` and DPoP / mTLS (§9.11), jwt-dpop grant | ID-JAGs with `cnf` refused |
| Multi-tenant Resource AS, `aud_tenant` (§6) | refused |
| `sub_id` and `aud_sub` subject resolution, JIT provisioning (§3.1, §3.2) | `iss` + `sub` via source connections, then `email` in the source's trusted domains; users aren't created |
| `authorization_details` (RFC 9396) | ignored |
| `act` from the ID-JAG carried into the access token | not carried |
| Comparing the metadata `issuer` with the URL-derived issuer when the source is saved (§9.5) | not checked; redemption binds `iss` to the URL |

## Running

```bash
# Stub IdP and verifier self-check (no DB):
uv run python tests/mcp_conformance_id_jag_issuer/selfcheck_resource_as.py
# Full acceptance against a disposable PostgreSQL container (never your dev DB):
tests/mcp_conformance_id_jag_resource_as/run-local.sh
```

Like the issuer suite, the files don't match pytest's `python_files`, so `make test` never collects them, and the runner doesn't load `local.env.yml`.
