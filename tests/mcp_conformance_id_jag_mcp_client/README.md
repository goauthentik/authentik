# MCP conformance: ID-JAG end to end through the official MCP TypeScript SDK

GitHub check: **`test-mcp-conformance (id-jag-mcp-client)`**, a third matrix row in `.github/workflows/ci-mcp-id_jag_issuer.yml`.

The other two suites test each half of the Identity Assertion JWT Authorization Grant (ID-JAG, draft-ietf-oauth-identity-assertion-authz-grant-06) against fixtures written for them. This one puts **authentik in both roles** and drives MCP Enterprise-Managed Authorization with an independent, real-world client: the official MCP TypeScript SDK, `@modelcontextprotocol/client`. The suite shows whether an MCP client built on the SDK works against authentik, and where it doesn't.

## What runs

```
Node harness (harness/, own lockfile)              authentik (live server)
-------------------------------------              -----------------------
MCP client: POST /mcp, no token ---> MCP server (server SDK, harness/mcp_server.mjs)
                                     401 + RFC 9728 metadata naming the Resource AS
SDK discovery: PRM, RFC 8414 metadata ------------> Resource AS provider (issuer check)
1. openid-client: OIDC code + PKCE ---------------> IdP provider -> ID token
2. SDK discoverAndRequestJwtAuthGrant ------------> IdP provider: token exchange -> ID-JAG
3. SDK CrossAppAccessProvider (jwt-bearer) -------> Resource AS provider -> access token
4. SDK Client + StreamableHTTPClientTransport ----> MCP server: verifies the token against
                                                    the Resource AS JWKS (jose), whoami
```

* **authentik, IdP Authorization Server**: an OAuth2 provider for the MCP client's application, with token exchange. A system agent links that application to the Resource AS issuer (`id_jag_audience`), the client's ID there (`id_jag_client_id`), and the MCP resource (`id_jag_resources`), as in the issuer suite.
* **authentik, Resource Authorization Server**: a second, confidential provider with the jwt-bearer grant. It trusts the IdP through an OpenID Connect source created through the admin API from the IdP's metadata URL. The user is connected to that source with their IdP subject.
* **`harness/run.mjs`**: the client. openid-client signs in (step 1), logging in through the flow executor API, since a browser isn't needed. Steps 2 to 4 use the SDK. A recording `fetch` keeps a redacted transcript of every request the SDK sends, including the client authentication it chose and the parameters (assertion, secrets and tokens are redacted). Credentials reach it over stdin, never argv or the environment, and every string it writes is scrubbed of them.
* **`harness/mcp_server.mjs`**: a minimal MCP server built on `@modelcontextprotocol/server`, with two endpoints, each with its own metadata:
  * `/mcp` is spec-compliant: it accepts only tokens issued for its resource (the server SDK's `expectedResource`, MCP "token audience binding", RFC 8707 §2).
  * `/mcp-issuer-bound` accepts any valid token from its authorization server (signature, `iss`, `exp`). It's the positive control for reaching an MCP server at all.
* **`harness/selfcheck.mjs`**: checks the MCP server fixture against a stub authorization server, with no authentik. It confirms that `/mcp` accepts a token for its resource and refuses one whose `aud` is a client ID, so a red `mcp.*` check reflects authentik's behavior, not the fixture's.
* **`acceptance_mcp_client.py`**: configures authentik, runs the harness once, and turns its observations into checks. It also checks, on authentik's side, that the subject the MCP server saw is the signed-in user.

## Checks

`catalog.py` lists 15 check IDs, one or more per step. The report format, statuses and gating are shared with the other suites (`checks.Report`). Negatives are gated on their positive controls: `exchange.id-jag` for the token-exchange negatives and `redeem.id-jag` for the replay.

| Check | Step | Result |
| --- | --- | --- |
| `config.authentik-both-roles` | setup | PASS |
| `mcp.discovery` | discovery | PASS |
| `sso.id-token` | 1 | PASS |
| `exchange.id-jag` | 2 | PASS |
| `exchange.scope-forwarding` | 2 | PASS (explicit `invalid_scope`) |
| `redeem.resource-bound` | 3 | **FAIL, expected** |
| `redeem.id-jag` | 3 | PASS |
| `redeem.client-auth-methods` | 3 | PASS |
| `mcp.tool-call` | 4 | PASS |
| `mcp.audience-bound` | 4 | **FAIL, expected** |
| `e2e.sdk-default` | 1 to 4 | **FAIL, expected** |
| `neg.exchange.wrong-audience` | 2 | PASS (`invalid_target`) |
| `neg.exchange.unregistered-resource` | 2 | PASS (`invalid_target`) |
| `neg.exchange.unlinked-app` | 2 | PASS (`invalid_target`) |
| `neg.redeem.replay` | 3 | PASS (`invalid_grant`) |

### Expected red

All three have one cause: authentik's Resource AS doesn't support RFC 8707 resource indicators yet. The separate `oauth2/resource-indicators` work adds `OAuth2Provider.allowed_resources`. These checks must stay red until then; don't make them pass by weakening authentik's validation.

* **`redeem.resource-bound`**: the SDK always sends `resource` (the MCP server's RFC 9728 resource) at token exchange. authentik allows it because it's on the agent's allow-list, and embeds it in the ID-JAG. The Resource AS then refuses the ID-JAG with `invalid_grant` (internally `resource_not_governed`), because §4.4.1 requires each `resource` to be one it governs and providers can't declare any. authentik doesn't return the cause, so the check redeems the same kind of ID-JAG without the `resource` claim right after. That one gets HTTP 200, which isolates the claim as the reason.
* **`mcp.audience-bound`**: even with an ID-JAG without `resource`, the SDK sends `resource=<MCP server>` with the jwt-bearer request. authentik ignores the parameter, as RFC 6749 §3.1 allows for unrecognized parameters, and issues a token whose `aud` is the client's `client_id`. A spec-compliant MCP server must refuse it, and the fixture does: 401 `invalid_token`. The SDK then re-authorizes once and gives up with "Server returned 401 after re-authentication".
* **`e2e.sdk-default`**: the SDK's documented flow, unmodified, fails at the jwt-bearer step for the reason above. The SDK retries `invalid_grant` once with a fresh ID-JAG, so two token exchanges and two jwt-bearer requests appear in the transcript.

To turn them green:

1. The Resource AS provider declares the MCP server URL as a governed resource (`allowed_resources`).
2. For an ID-JAG `resource` claim (§4.4.1), and for the RFC 8707 `resource` parameter on the jwt-bearer request, authentik checks the value against the governed resources. If the value isn't governed, authentik refuses with `invalid_grant` for the claim and `invalid_target` for the parameter.
3. authentik issues the access token with `aud` set to that resource.

Nothing on the IdP side needs to change.

## Where the SDK forced a decision

| Behavior of `@modelcontextprotocol/client` 2.4.0 | Decision |
| --- | --- |
| `requestJwtAuthorizationGrant` and `discoverAndRequestJwtAuthGrant` always send `resource`; there's no way to omit it (an omitted one is sent as the string `undefined`). | The spec makes `resource` OPTIONAL (§4.3), and the positive controls for steps 3 and 4 need an ID-JAG authentik can redeem. Their assertion callback therefore makes its own RFC 8693 request without `resource`, in the SDK's shape (`client_secret_post`). `CrossAppAccessProvider` explicitly supports custom assertion callbacks. Discovery, the jwt-bearer step and the MCP transport stay SDK code. The unmodified flow is `e2e.sdk-default`. |
| Token exchange authenticates with `client_secret_post`, with no option to change it. | authentik accepts it; nothing to decide. |
| `CrossAppAccessProvider`'s jwt-bearer request picks `client_secret_basic` from the metadata. Okta's sample overrides it to `client_secret_post`. | authentik advertises and accepts both; `redeem.client-auth-methods` checks each through `exchangeJwtAuthGrant`. |
| The jwt-bearer request carries `resource` from the protected resource metadata. | Spec-correct (RFC 8707); authentik ignores it today. Reported in `redeem.id-jag` notes and failed in `mcp.audience-bound`. |
| `CrossAppAccessProvider` passes the MCP scope (from `WWW-Authenticate` or the metadata's `scopes_supported`) to the assertion callback, and the SDK's examples forward it. Okta's sample even forces one. | authentik refuses any `scope` on ID-JAG requests with `invalid_scope`. RFC 8693 §2.2.2 allows that, and it's explicit rather than silent, so `exchange.scope-forwarding` passes with a note. The MCP server's metadata advertises no `scopes_supported`, so the main flow doesn't trip over it. A real MCP server that advertises scopes would make the SDK's default flow fail at token exchange. |
| RFC 8414 discovery drops the issuer's trailing slash when inserting the well-known path. authentik issuers end in `/`, and authentik serves the path-insertion form with the slash kept. | RFC 8414 §3.1 inserts the well-known string before the path component as it is, slash included, so authentik is right. The SDK falls back to the OpenID Connect suffix form, which works; `mcp.discovery` records the 404s in a note. |
| The SDK parses authorization server metadata through a schema that drops unknown members. It never looks at `authorization_grant_profiles_supported` (§7.2) before using jwt-bearer. | `mcp.discovery` checks the profile in the document authentik served, not the SDK's parsed copy. |
| `CrossAppAccessProvider` without `expectedIssuer` is deprecated: the MCP server would choose where the client's credentials go. | The harness passes the Resource AS issuer from discovery. |
| Okta's sample strips the trailing slash from `audience`. | Not done here. Draft-06 §4.3 uses the Resource AS issuer identifier, compared exactly. authentik's issuers end in `/`, so a client that strips it gets `invalid_target`. |

The `neg.exchange.unlinked-app` refusal is `invalid_target`. Draft-06 §4.3.4.3 profiles `access_denied`, and RFC 8693 §2.2.2 allows `invalid_target`. As in the issuer suite, it passes with a note.

## Not implemented yet

| Rule | Status |
| --- | --- |
| Governed `resource` and audience-restricted access tokens at the Resource AS (§4.4.1, RFC 8707) | refused or ignored; three checks are red |
| `scope` on ID-JAG token exchange (§4.3) | refused with `invalid_scope` |
| Sender-constrained ID-JAGs (`cnf`, DPoP) | not exercised; the SDK's Cross-App Access helpers don't use DPoP |
| JIT provisioning at the Resource AS (§3.2) | the user must already be connected to the IdP source |
| A browser-driven sign-in | step 1 logs in through the flow executor API; the authorization code + PKCE flow and ID token validation are openid-client's |

## Pinned versions

`package.json` and `pnpm-lock.yaml` live in this directory, which is its own pnpm root (`pnpm-workspace.yaml`), outside the repository's workspaces. No dependency may run install scripts.

* `@modelcontextprotocol/client` and `@modelcontextprotocol/server` **2.4.0**: the 2.x line is now stable, not the 2.0.0 alpha that Okta's write-up uses. The API it describes is unchanged: `CrossAppAccessProvider`, `discoverAndRequestJwtAuthGrant`, `requestJwtAuthorizationGrant`, `exchangeJwtAuthGrant`, `Client` and `StreamableHTTPClientTransport`.
* `openid-client` 6.8.8 and `jose` 6.2.13.
* Node 24 (nvm `v24.22.2` locally).

## Running

```bash
# MCP server fixture self-check (no authentik, no DB):
pnpm --dir tests/mcp_conformance_id_jag_mcp_client install --frozen-lockfile
pnpm --dir tests/mcp_conformance_id_jag_mcp_client run selfcheck
# Full acceptance against a disposable PostgreSQL container (never your dev DB):
tests/mcp_conformance_id_jag_mcp_client/run-local.sh
```

The runner uses throwaway database names, an ephemeral secret key and its own `AUTHENTIK_ENV`, and doesn't load `local.env.yml`. Each run writes to a fresh `results/<UTC timestamp>-<pid>/`, which is gitignored:

* `report.json`, `report.md` and `checks.junit.xml`, as in the other suites. Each check's details include the redacted HTTP transcript for that step.
* `harness.json`: the harness's raw observations.
* `harness.stderr.log`.

Like the other suites, the Python file doesn't match pytest's `python_files`, so `make test` never collects it.
