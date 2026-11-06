# MCP conformance: authentik as ID-JAG issuer

GitHub check: **`test-mcp-conformance (id-jag-issuer)`**, from `.github/workflows/ci-mcp-id_jag_issuer.yml`.

This is a live acceptance check for authentik in the **IdP Authorization Server** role of MCP Enterprise-Managed Authorization. authentik issues an Identity Assertion JWT Authorization Grant (ID-JAG) through RFC 8693 token exchange, and a separate Resource Authorization Server redeems it to get an access token for an MCP server. The check fails until authentik implements ID-JAG issuance.

## What runs

```
MCP client (harness)                authentik (live server)          resource_as.py (separate process)
--------------------                -----------------------          ---------------------------------
POST /mcp (no token) ------------------------------------------------> 401 WWW-Authenticate resource_metadata
GET PRM, GET RAS metadata (issuer check) ----------------------------> RFC 9728 / RFC 8414
login via flow executor API -------> identification+password stage
authorize (code+PKCE), token ------> ID Token
token exchange (id_token -> id-jag) -> ID-JAG (typ oauth-id-jag+jwt)
POST /token jwt-bearer + Basic --------------------------------------> verifies the ID-JAG against authentik
                                                                       (discovery from iss -> jwks_uri) -> Bearer AT
POST /mcp initialize, tools/call whoami (Bearer AT) -----------------> 200, identity = ID-JAG sub
```

* **authentik**: every request goes to production views over real HTTP (Django `StaticLiveServerTestCase`). Nothing in authentik is mocked. Test setup provisions the objects through the ORM: a user, a login flow, two confidential OAuth2 providers/applications, and, when the model supports it, two system agents carrying the ID-JAG trust configuration from goauthentik/authentik#26973.
* **`resource_as.py`**: the Resource AS and protected MCP resource, both test infrastructure. It uses only the stdlib and `cryptography` primitives. JWS parsing, JWK conversion, signature verification and claim validation are written here, so neither authentik nor PyJWT/jwcrypto/authlib validates authentik's output; `selfcheck_resource_as.py` enforces this with an AST import guard. Signing keys are found from the ID-JAG issuer identifier alone: RFC 8414 path-insertion metadata first, then OpenID Connect Discovery as the fallback that draft-06 §7.1 allows.
* **`selfcheck_resource_as.py`**: 16 unittest cases that need neither authentik nor a database. A stub IdP signs assertions with `cryptography`, on a separate code path from the verifier. The cases cover:
  * the positive controls: RS256, ES256, a single-element `aud` array, the full flow through to an MCP call, and the 401 challenges;
  * the rejection matrix: `typ`, `alg` none/HS256, a foreign key, a tampered payload, an unknown `kid`, `iss`, `aud` (wrong, or a 2-element array), `client_id` binding, missing `sub`/`jti`/`exp`/`iat`, expired, future `iat`, an ungoverned `resource`, `jti` replay, client auth, `grant_type`, and a metadata issuer mismatch.

## Pass criteria

`checks.py` lists 21 check IDs. The run passes only if every ID is executed exactly once and every result is `PASS`. These all fail the run:

* `FAIL` or `ERROR` (a harness exception is recorded, not swallowed);
* `BLOCKED`: a prerequisite did not pass. Negatives are gated on the positive control (`exchange.id-jag-issued`), so "authentik rejects everything" cannot pass them vacuously;
* missing, duplicate or unknown IDs, and zero checks;
* a missing report: the workflow's *Verify structured report* step checks for it separately.

SHOULD-level and OPTIONAL observations are recorded as `notes` and never change a status. Examples: whether `identity_chaining_requested_token_types_supported` is advertised, `email`/`aud_sub`, `act`, `expires_in`, and `refresh_token`.

Artifacts go to `results/`, which is gitignored; CI can override the location with `MCP_CONFORMANCE_RESULTS_DIR`:

* `report.json`: per check, the status, summary, details (HTTP status, redacted body, decoded claims), notes, spec refs and the upstream analogue;
* `report.md`, which also becomes the job summary;
* `checks.junit.xml`, with one testcase per check;
* `resource_as.events.jsonl`: each Resource AS/MCP decision with the failing rule;
* `resource_as.stderr.log`.

Tokens, assertions and client secrets are never written. Response bodies show them only as `<redacted len=N>`. The fixture config file holding the Resource AS client secrets lives in a temporary file that is deleted after startup.

## Running

```bash
# Fixture self-check (no DB):
uv run python tests/mcp_conformance_id_jag_issuer/selfcheck_resource_as.py
# Full acceptance against a disposable PostgreSQL container (never your dev DB):
tests/mcp_conformance_id_jag_issuer/run-local.sh
# Or with an already-disposable database (CI):
AUTHENTIK_POSTGRESQL__TEST__NAME=test_authentik_mcp_id_jag_issuer \
  uv run manage.py test tests/mcp_conformance_id_jag_issuer/acceptance_id_jag.py
```

None of the files match `python_files` (`tests.py`, `test_*.py`, `*_tests.py`), so `make test` and `manage.py test tests` never collect them. Verified: `pytest --collect-only tests` collects 94 items and none of them are from this directory; only an explicit path collects `IdJagIssuerAcceptance::test_id_jag_issuer`. No public network services are used. Everything binds to localhost, and the runner needs no browser, web build, Go or Rust.

## Provenance

| Source | Pin | Used for |
| --- | --- | --- |
| draft-ietf-oauth-identity-assertion-authz-grant **-06** (31 Oct 2026, latest; -07 does not exist) | `https://www.ietf.org/archive/id/draft-ietf-oauth-identity-assertion-authz-grant-06.txt`, sha256 `1699586519ecb5333fb48ee0443f57d56e95f0b745e25b70e925fb85a6efcfc0` | Normative basis for all checks (§3.1, §4.3, §4.3.3, §4.3.4(.3), §4.4.1, §5.1, §7.1/7.2, §9.5/9.6) |
| draft -04 (21 May 2026) | sha256 `a59c1dffc0b5e59d1bd541276c6948eb9191f3b83685be5810a32e63effb4653` | Comparison only (see below) |
| RFC 8693 §2.2.1/§2.2.2, RFC 7523 §3, RFC 7521 §5.2, RFC 8414 §3.3, RFC 9728 §3.3, RFC 8725 §3.11, RFC 6749 §5.1/§5.2 | published RFCs | Response/error rules and Resource AS processing |
| MCP Enterprise-Managed Authorization, stable `2026-07-28` | `modelcontextprotocol/ext-auth@15ca394e00a66434520b9ade26294999295a43ae` `specification/stable/enterprise-managed-authorization/2026-07-28/enterprise-managed-authorization.mdx` | `resource` = MCP server resource, access token audience-restricted to it, client_secret_basic, `authorization_grant_profiles_supported` |
| Upstream MCP conformance | `modelcontextprotocol/conformance@c37eec888e1c6ff140af79987a40008548b7cc5f` `src/scenarios/client/auth/enterprise-managed-authorization.ts` (sha256 `caec7e9a…0383c2`) | Check-ID analogues and the Resource AS checks it performs: typ, aud with or without trailing slash, client_id continuity, resource = MCP URL, Basic auth |
| authentik feature | goauthentik/authentik#26973 `providers/oauth2/id-jag` @ `dce0a00534cb51ebe24d6a8f96ef3bc868006200` (open, unmerged) | Shape of the provisioning (system `Agent` with `applications`, `id_jag_audience`, `id_jag_client_id`, `id_jag_resources`). No production code is copied or cherry-picked |

**How upstream is used, and how it isn't.** The upstream scenario is a *client* test: it mocks both the IdP and the Resource AS, and its mock AS doesn't even verify the ID-JAG against the IdP's key, because it signs with an ephemeral per-user key. No upstream suite targets an issuer. Running the upstream mock flow would therefore test nothing in authentik, so it is **not run**. Instead, `resource_as.py` re-implements that mock AS's checks in Python against the *real* authentik issuer and adds the draft-06 §4.4.1 rules upstream skips (issuer trust, JWKS signature, aud array cardinality, exp/iat, jti). `checks.CATALOG` records the upstream analogue on each check: `complete-flow-token-exchange` maps to `exchange.id-jag-issued`, and `complete-flow-jwt-bearer` maps to `ras.redeem`.

### -04 vs -06, and the choice of -06

The MCP EMA stable profile (2026-07-28) links -04; this check pins -06. The differences that affect outcomes:

| Topic | -04 | -06 | This check |
| --- | --- | --- | --- |
| Error for an invalid subject token (wrong audience, bad signature) | non-normative example uses `invalid_grant` | §4.3.4.3 profiles `invalid_request`, "as required by Section 2.2.2 of RFC 8693" | `invalid_request`. RFC 8693 §2.2.2 says the error "MUST be the invalid_request error code" in either revision, so this isn't a -06-only tightening |
| Multiple `audience` values | not addressed | §4.3.3 MUST `invalid_request` | `invalid_request` |
| Unknown audience / ungoverned resource | not addressed | §4.3.3 MUST `invalid_target` | `invalid_target` |
| Client not authorized for a trusted audience | not addressed | §4.3.4.3 profiles `access_denied` (but "any OAuth error code MAY be returned") | `access_denied` **or** `invalid_target` accepted; a mismatch with the profile is recorded as a note |
| Tokens issued for other purposes as subject | not explicit | §4.3.3 MUST NOT accept access tokens, ID-JAGs or client assertions as identity assertions | enforced |
| `scope` semantics | "scopes at the Resource Server" | §4.3: Resource AS meaning, not OIDC; §4.3.3 MUST include granted values | `exchange.scope-semantics`: a separate check, so it can't mask the core flow |

Checks are never relaxed to fit an implementation. Where -06 says "MAY return any code", the check accepts more than one code and says so explicitly.

## Reuse when combining the three MCP branches

These parts don't depend on ID-JAG and can be moved to a shared `tests/mcp_conformance/` package:

* `checks.py`: `Report`, `CheckResult`, `verdict()` (strict catalog matching) and the JSON/Markdown/JUnit writers. Only `CATALOG` is feature-specific.
* `resource_as.py`: the JOSE verifier (`parse_compact_jws`, `jwk_to_public_key`, `verify_signature`), `IssuerKeys` (metadata discovery with the issuer check, JWKS), and the MCP protected resource (PRM, 401 challenge, minimal Streamable HTTP JSON-RPC). Only the `IdJagValidator` and `/token` jwt-bearer handling are ID-JAG-specific.
* `acceptance_id_jag.py`: the live-server plumbing (`_pre_setup`/`_post_teardown`, `FixtureProcess`, `run_check` with BLOCKED gating, redaction) and `sso()`, which logs in for real through the flow executor API and runs code+PKCE without a browser.
* The workflow: the matrix shape `test-mcp-conformance (<name>)`, the report-verification step and the artifact layout. These are ready to merge into one workflow with one matrix row per feature.
