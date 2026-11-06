# HANDOFF: test-mcp-conformance (id-jag-issuer)

I cannot create issues or PRs, but I can help you write the content for them.

## Proposed PR

**Title:** `tests: add MCP conformance acceptance check for ID-JAG issuance (id-jag-issuer)`

**Body:**

> Adds a standalone acceptance check, `test-mcp-conformance (id-jag-issuer)`, that exercises authentik as the IdP Authorization Server of draft-ietf-oauth-identity-assertion-authz-grant-06 (MCP Enterprise-Managed Authorization):
>
> 1. A real login through the flow executor API, then authorization code + PKCE to get an ID Token.
> 2. Token exchange `requested_token_type=urn:ietf:params:oauth:token-type:id-jag` at authentik's token endpoint.
> 3. An independent Resource AS fixture verifies the ID-JAG. It is stdlib + `cryptography` only and discovers keys from authentik's issuer, then redeems the ID-JAG via RFC 7523 jwt-bearer.
> 4. The resulting access token is used at a protected test MCP resource.
> 5. Negative cases cover wrong-client and tampered subject tokens, access tokens and ID-JAGs presented as subject tokens, unknown, multiple and unauthorized audiences, an ungoverned resource, and missing client auth.
>
> The check is test-only and contains no production changes. It is intentionally red on `main` until ID-JAG issuance lands (see goauthentik/authentik#26973), and is meant to be carried onto the feature branch. It must not be made required before then. Test files are not named `test_*.py`, so general test discovery doesn't pick them up. Details, spec provenance and the -04/-06 differences are in `tests/mcp_conformance_id_jag_issuer/README.md`.
>
> 🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Files

* `.github/workflows/ci-mcp-id_jag_issuer.yml`: `pull_request` (main, version-*) + `workflow_dispatch`
* `tests/mcp_conformance_id_jag_issuer/`:
  * `acceptance_id_jag.py`: the live authentik harness
  * `resource_as.py`: the independent Resource AS + MCP resource fixture
  * `selfcheck_resource_as.py`: fixture controls and rejection matrix
  * `checks.py`: catalog, strict verdict and report writers
  * `run-local.sh`: local runner with a disposable Postgres
  * `README.md`, `HANDOFF.md`, `.gitignore`, `__init__.py`

## Expected current failure (actual result on `main` @ eb3832a818)

The check fails meaningfully: 3 PASS, 2 FAIL, 16 BLOCKED, 0 ERROR.

* `capability.agent-id-jag-config` **FAIL**: "enterprise Agent has no ID-JAG trust configuration (missing fields: applications, id_jag_audience, id_jag_client_id, id_jag_resources)". The fields are detected with `_meta.get_field`, so this is not an ImportError or FieldError.
* `exchange.id-jag-issued` **FAIL**: authentik answers `HTTP 400 invalid_target` because main rejects the `resource` parameter. The exchange is still sent, so this is authentik's real protocol response.
* `discovery.mcp-prm`, `discovery.idp-metadata`, `sso.id-token` **PASS**. Real SSO yields an ID Token that the independent verifier accepts against authentik's JWKS, so the harness itself works.
* Everything downstream, including all negatives, is **BLOCKED**: no positive control means no meaningful negative. The observed response is still recorded for each.

## Actual result against the feature (PR #26973 head dce0a005, scratch worktree, not committed)

The test directory was copied onto a temporary detached worktree of the PR head and run there. That worktree has been removed. Result: 15 PASS, 6 FAIL.

* **PASS:**
  * `capability.agent-id-jag-config`
  * discovery ×2 and `sso.id-token`
  * `exchange.id-jag-issued`: `token_type=N_A`, `issued_token_type=id-jag`, `no-store`
  * `assertion.jose`: `typ=oauth-id-jag+jwt`, RS256 signature verified independently
  * `assertion.claims`: `aud` = Resource AS issuer, `client_id` = id at the Resource AS, `resource` exact, `sub` = SSO user, `act.sub` = system agent
  * `assertion.not-a-bearer-token`
  * `ras.client-binding`, `ras.redeem`, `mcp.access`
  * `negative.unknown-audience`, `negative.resource-not-governed`, `negative.client-not-authorized-for-audience` (note: `invalid_target` rather than the -06-profiled `access_denied`), `negative.no-client-auth`
* **FAIL** (real spec deviations in the PR, not harness problems):
  1. `negative.access-token-as-subject`: **authentik issued an ID-JAG** when given its own *access token* labeled `subject_token_type=id_token`. draft-06 §4.3.3 says this MUST NOT be accepted. This is the most important finding. A likely cause, not yet confirmed: `validate_id_token` accepts any JWT signed by the provider with `aud=client_id` whose `jti` matches a stored token.
  2. `negative.wrong-client-id-token`, `negative.tampered-id-token`, `negative.id-jag-as-subject`: `invalid_grant` instead of `invalid_request`. RFC 8693 §2.2.2 requires `invalid_request`, and draft-06 §4.3.4.3 also profiles it. The PR follows the -04 example.
  3. `negative.multiple-audiences`: `invalid_target` instead of `invalid_request` (draft-06 §4.3.3 MUST).
  4. `exchange.scope-semantics`: the requested Resource-AS scope `mcp:tools` is silently dropped, because it is clamped to authentik ScopeMappings. The ID-JAG has no `scope` claim and the response has no `scope` (draft-06 §4.3, §4.3.3, §4.3.4).
* Notes (SHOULD-level, don't fail): `identity_chaining_requested_token_types_supported` is not advertised (§7.1), and neither `email` nor `aud_sub` is present (§3.1).

The PR-head run happened before one last gating tweak: `exchange.id-jag-issued` is no longer gated on provisioning. That only changes BLOCKED versus FAIL labelling on `main`, which the final `run-local.sh` run confirmed above.

## Validation performed

* `selfcheck_resource_as.py`: 16/16 OK.
* `uv run black --check`, `uv run ruff check`, `uv run mypy --strict`, `uv run bandit -c pyproject.toml -iii` on the directory: clean.
* actionlint v1.7.7: clean, except for the unknown runner label `ubuntu-26.04`. That label is already used throughout `ci-main.yml` and is simply newer than this actionlint.
* Collection: `pytest --collect-only tests` collects 94 items and none are from this directory. The directory alone collects 0, and the explicit file collects 1.
* `make lint-spellcheck` could not run locally (npm `EBADDEVENGINES`, an environment problem); not validated.
* All database runs used a disposable `postgres:16` container on a random localhost port with a dedicated test DB name. The developer database was never used.
* Artifacts were grepped for JWTs (`eyJ`) and secrets: there are none. Bodies show `<redacted len=N>`.
* **Not validated:** the workflow has not run on GitHub Actions (nothing was pushed). Codecov upload behaviour (`./.github/actions/test-results`) is therefore untested.

## Limitations

* Provisioning goes through the ORM, because the agent API requires an enterprise license. Only the protocol endpoints are exercised as production endpoints. Field names follow PR #26973 at dce0a005. If the final model differs, update `check_capability` (one function).
* The Resource AS and MCP resource are a minimal independent implementation, not the official MCP SDK. Covered: Streamable HTTP JSON responses only, no SSE, client_secret_basic only, opaque access tokens, and single-use `jti` (a fixture policy).
* Not covered: SAML or refresh-token subjects, DPoP/mTLS-bound ID-JAGs (§9.11), RAR `authorization_details`, multi-tenant `tenant`/`aud_tenant`, and actor_token behaviour (out of scope per -06).
* The RFC 8414 strict path (no trailing slash) returns 404 on authentik. The fixture finds metadata through the trailing-slash variant, which is recorded in the report.

## Follow-ups

* Report the access-token-as-subject acceptance to the PR #26973 author. It is security-relevant (token confusion).
* Decide whether to align error codes with RFC 8693 §2.2.2 / draft-06, or to pin the check to -04 semantics. The recommendation is -06, because RFC 8693's MUST applies in either case.
* When combining the three MCP branches, extract the shared pieces listed in the README section "Reuse when combining the three MCP branches".
