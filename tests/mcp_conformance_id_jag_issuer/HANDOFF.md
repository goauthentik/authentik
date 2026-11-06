# HANDOFF: ID-JAG issuer acceptance on Jens's branch

I cannot create issues or PRs, but I can help you write the content for them.

## Current status after merging the issuance fixes (2026-11-06)

- Conformance PR: goauthentik/authentik#27677, branch `t3/id-jag-issuer`, targeting `providers/oauth2/id-jag`.
- Exact feature base: `93fbedebdd42dd0a6d2f58ed6b4571df4d231145`.
- Exact tested merge commit: `b7d3a776a5024c836cd90a43baef72213d5d9c8c`, merging the feature base into conformance head `203eb0bc834779210f4b0f493e2290d3969613a2`. Git merged the fetched branches cleanly without manual conflict edits or rewritten history.
- Fresh local acceptance: **21 PASS / 0 FAIL / 0 ERROR / 0 BLOCKED**, all 21 check IDs unique, report generated **2026-11-06 16:01:48 UTC**. Django acceptance test passed in 63.17 seconds; independent fixture self-check: **16 tests, OK**.
- Evidence (gitignored): [report](results/merged-b7d3a776/report.md), [JSON](results/merged-b7d3a776/report.json), [JUnit](results/merged-b7d3a776/checks.junit.xml), [fixture decisions](results/merged-b7d3a776/resource_as.events.jsonl). Run log: `/tmp/id-jag-merged-b7d3a776.log`. Scanning these files found no compact JWTs or private-key blocks.
- The run used `UV_NO_SYNC=1`, the existing virtual environment, and the runner's disposable PostgreSQL container and isolated configuration. It did not use the developer database. These are local results, not evidence of GitHub Actions success.
- Black, Ruff, shell syntax and whitespace checks passed. Explicit acceptance collection found one test. Strict mypy passed on all five harness Python files. One initial mypy invocation loaded the default local configuration through its plugin; no configuration contents were printed. It was rerun with an explicit isolated `AUTHENTIK_ENV`.
- The later documentation/comment changes remove obsolete expected-failure wording. Test assertions, fixture behavior, and workflow triggers are unchanged. The PR diff against the feature base contains only tests, CI and documentation.

The original six failures are addressed by the feature branch. Invalid subjects and multiple audiences now return `invalid_request`, and the access-token-as-ID-Token request is rejected. The scope check passes because requested Resource AS scopes are explicitly refused with `invalid_scope`; this is not support for granting `mcp:tools`. Clients must omit nonempty scope requests until an explicit grant policy is implemented.

Coverage still pins draft-06 while MCP EMA references draft-04. Passing these 21 checks is not complete protocol certification: the existing trusted-federation JWT/access-token subject path and other coverage limits below remain review topics.

Reproduce with a new results directory:

```bash
UV_CACHE_DIR=/tmp/id-jag-uv-cache UV_NO_SYNC=1 \
  tests/mcp_conformance_id_jag_issuer/run-local.sh
```

Suggested current PR description:

> Adds a dedicated Actions check for ID-JAG issuance, independent JWT verification/redemption, and protected MCP access, plus negative requests. It follows the existing OpenID conformance setup/results conventions and runs on PRs targeting feature branches. The suite remains outside general test discovery and has a disposable PostgreSQL local runner.
>
> On feature commit `93fbedebdd42dd0a6d2f58ed6b4571df4d231145`, local validation passes all 21 acceptance checks and 16 fixture self-checks. Scope requests are explicitly refused with `invalid_scope`. The suite pins draft-06; HANDOFF.md explains draft-04 differences and coverage limits. Hosted Actions results must be assessed separately.

## Historical baseline before the issuance fixes

The following sections preserve the original observations on `dce0a00534`, including the original proposed PR text. Their six failures and publication status describe that earlier snapshot, not the current branch.

## Branch and evidence (historical)

- Working branch: `t3/id-jag-issuer`; nothing pushed, no issue/PR created, no message or comment sent.
- Target: Jens/BeryJu's [PR #26973](https://github.com/goauthentik/authentik/pull/26973), branch `providers/oauth2/id-jag`.
- Exact feature base, verified through GitHub metadata and a fresh fetch: `dce0a00534cb51ebe24d6a8f96ef3bc868006200`.
- Original tests: `5231141cff0053368e04e5f57d421ee2797701fa` and `f0b65c700b388fa9c384a3084971d8ad46063e7d`, based on `eb3832a8185452152c5cd544635a8413716014ce`.
- Backup ref: `backup/id-jag-issuer-before-jens-rebase-20261106`, pointing to `f0b65c700b388fa9c384a3084971d8ad46063e7d`.
- Rebase replayed exactly those two commits, without conflicts, as `951d0780fb` and `38a417be71`; `git range-diff` confirms unchanged patches. Jens's source branch was not altered.
- Exact test/runner SHA validated: **`416e64113f9741e726a0c65b9eeb36f639b11ee0`**. Later changes update documentation and align workflow triggers/concurrency/Codecov grouping and coverage failure propagation with OpenID conformance; the live test and local runner are unchanged; the final branch HEAD is available with `git rev-parse HEAD`.
- Final live report generated **2026-11-06 13:44:02 UTC**: **15 PASS / 6 FAIL / 0 BLOCKED / 0 ERROR**, all 21 expected check IDs present exactly once. Exit code 1 is intentional.
- Local evidence (gitignored): [report](results/validated-rebase/report.md), [structured diagnostics](results/validated-rebase/report.json), [JUnit](results/validated-rebase/checks.junit.xml), [Resource AS decisions](results/validated-rebase/resource_as.events.jsonl), [run log](results/validated-rebase-run.log), [artifact audit](results/artifact-audit.json).

The diff against Jens's exact head contains only tests, their workflow, and documentation. `pull_request:` has no base-branch filter, so a future PR targeting `providers/oauth2/id-jag` triggers the check. Push triggers (`main`, `next`, `version-*`), concurrency policy, and the Codecov `conformance` flag now match OpenID conformance in `CI - Main`; setup, coverage execution, and result uploading already use the same shared actions. The dedicated workflow preserves feature-base PR coverage without broadening all other CI jobs. No branch-protection setting is changed.

## Fresh observed results and interpretation

The complete real flow passes: login and code+PKCE, ID-JAG issuance, independent signature and claim verification using discovered JWKS, client binding at the separate Resource AS, JWT-bearer redemption, and an authenticated MCP `tools/call`. The check does not pass merely because invalid inputs are rejected. All negative cases have a successful issuance prerequisite.

| Check | Observed on the tested feature head | Expected / classification |
| --- | --- | --- |
| `negative.access-token-as-subject` | HTTP 200, a new ID-JAG, when the actual SSO `access_token` is submitted with `subject_token_type=id_token` | Must reject the token-purpose mismatch. Explicit draft-06 §4.3.3 prohibition; RFC 8693 §2.1 already requires validation for the indicated token type. Security-relevant token confusion, not a fixture failure. The same end-user/client is used; this does not demonstrate cross-user escalation. |
| `negative.wrong-client-id-token` | HTTP 400 `invalid_grant` | Expected `invalid_request` under RFC 8693 §2.2.2 and draft-06 §4.3.4.3. Token is rejected; this is an error-code discrepancy. Client B's signature is independently verified using client A's JWKS, and its audience is client B. |
| `negative.tampered-id-token` | HTTP 400 `invalid_grant` after changing `sub` without re-signing | Expected `invalid_request` on the same basis. Invalid signature is rejected. |
| `negative.id-jag-as-subject` | HTTP 400 `invalid_grant` for the issued ID-JAG labeled as an ID Token | Expected `invalid_request` on the same basis. This ID-JAG also has the Resource AS audience; this probe does not independently prove a token-type rejection rule. |
| `negative.multiple-audiences` | HTTP 400 `invalid_target` for two audience parameters | Draft-06 §4.3.3 explicitly requires `invalid_request`. This is a -06-specific expectation; -04 does not define it and generic RFC 8693 allows multiple targets. |
| `exchange.scope-semantics` | HTTP 200 for requested `mcp:tools`, with neither an ID-JAG `scope` claim nor a response `scope` | Both -04 and -06 §4.3.3/§4.3.4 and RFC 8693 §2.2.1 require consistent granted scopes and disclosure when changed. Granting no scopes is a policy choice; silently changing them is the defect. The harness accepts `invalid_scope` or a consistently disclosed grant/reduction, and does not demand that `mcp:tools` be granted. |

**Common baseline versus draft changes.** The three subject-error checks use the specific RFC 8693 §2.2.2 `MUST invalid_request`, referenced explicitly in -06. RFC 8693 also permits other error codes “as appropriate”; -06 says any OAuth error code MAY be returned, while profiling this specific case. Draft-04 has a contradictory non-normative `invalid_grant` audience-validation example. These are interoperability findings under the suite's stated reading, not three token-acceptance vulnerabilities. The scope disclosure requirement exists in both drafts. The explicit token-purpose prohibition and multiple-audience error rule are additions in -06. This suite therefore must not be presented as an unqualified test of MCP EMA's linked -04 profile.

**Source inspection, without production edits.** `token/token_exchange.py::validate_id_token` validates a provider signature and client audience, then matches `jti` against the stored ID Token associated with an AccessToken. It does not check the submitted token's purpose or exact identity as that stored ID Token, consistent with the observed access-token confusion. Its invalid-subject `invalid_grant` branch is also present in the original `eb3832a818` token-exchange implementation; these error-code findings are not claimed as newly introduced regressions. `resolve_id_jag_audience` returns `invalid_target` for any audience count other than one. `token/base.py::check_scopes` intersects requested scopes with provider ScopeMappings; `views/token.py::create_id_jag_response` omits both an empty scope claim and the response scope. These explain the observations, without requiring a policy to grant an unconfigured scope.

**Fixture policy and informational notes.** Single-use `jti`, 30 seconds of clock leeway, the supported algorithms, test client registrations, and the `mcp:tools` scope are local fixture choices. They are not reported as feature defects. `invalid_target` for a trusted audience denied to this client passes with a note about -06's profiled `access_denied`. Missing `identity_chaining_requested_token_types_supported`, and missing `email`/`aud_sub`, are notes, not failures. Strict RFC 8414 discovery without the trailing slash returns 404; the fixture records its successful trailing-slash lookup.

## Harness corrections

- The original wrong-client probe used a different signing key and could test only signature rejection. Both clients now share a key, with independent verification of client B's token and a different audience before negative probes run. Failure to obtain/verify that token is a setup failure and blocks dependent checks.
- `run-local.sh` now generates its own ephemeral secret key and chooses a unique `AUTHENTIK_ENV`; it does not load `local.env.yml`. Database host, port, user, password, name, and test name point to its newly created disposable container. Neither the developer database nor its credentials were used.
- Local runs preserve earlier diagnostics in separate result directories and refuse an explicit directory already containing a report, avoiding stale-report confusion after a failed run.
- The local runner and workflow suppress captured production request logs in pytest failure output/JUnit. Structured token/secret response fields remain redacted. The artifact audit found no compact JWTs, unredacted structured token/secret fields, or private-key blocks.
- No production behavior or conformance expectation was changed. The first corrected run at `c9ba499294eb4a53324a46bef7e549f245f3ba39` also produced 15 PASS / 6 FAIL; the final run validates the result-directory correction as well.

## Validation and runnable commands

The final live command was:

```bash
UV_CACHE_DIR=/tmp/id-jag-uv-cache UV_NO_SYNC=1 \
  MCP_CONFORMANCE_RESULTS_DIR="$PWD/tests/mcp_conformance_id_jag_issuer/results/validated-rebase" \
  tests/mcp_conformance_id_jag_issuer/run-local.sh \
  > tests/mcp_conformance_id_jag_issuer/results/validated-rebase-run.log 2>&1
```

For a new run, omit `MCP_CONFORMANCE_RESULTS_DIR` to get a fresh timestamped directory, or select another empty directory. The runner also executes the independent self-check. This run used the existing `.venv` without syncing dependencies: Python 3.14.10, Django 5.2.19, pytest 9.2.0. It is local execution, not a lockfile-fresh CI environment.

- Independent `selfcheck_resource_as.py`: **16 tests, OK**, final run 2.228 seconds, before starting the Django acceptance test. Requires loopback socket permissions but no database.
- Black check, Ruff, strict mypy: passed on all five Python files.
- Bandit at the repository's `-iii` confidence threshold: passed (lower-confidence findings are excluded, not claimed absent).
- `bash -n run-local.sh`, `git diff --check`: passed.
- Workflow alignment check: push branches, concurrency, runner, shared action pins, and Codecov flag match `CI - Main` / OpenID conformance; unrestricted feature-base PR triggers remain. Coverage-report errors are no longer suppressed.
- actionlint 1.7.7: only its outdated unknown `ubuntu-26.04` runner-label diagnostic. Passed when ignoring that exact diagnostic. No workflow syntax/expression finding remains.
- Collection: general `tests` collects **92** tests, none from this suite; this directory collects **0**; explicit `acceptance_id_jag.py` collects **1**.
- `make lint-spellcheck`: unavailable locally (`cspell: command not found`; Make also reported the sandboxed default uv-cache lock). No spelling result is claimed; see [log](results/spellcheck.log).
- Both local acceptance runs used disposable `postgres:16` containers on random loopback ports; cleanup was confirmed. Fresh logs show no `local.env.yml` load.
- **GitHub Actions has never run this workflow.** Hosted runner setup, artifact upload, and Codecov behavior remain unvalidated. Nothing was pushed.

Reproduce static checks without loading developer configuration:

```bash
export AUTHENTIK_ENV=idjag-static-check AUTHENTIK_SECRET_KEY=idjag-static-check-only
export AUTHENTIK_LOG_LEVEL=warning
uv run python tests/mcp_conformance_id_jag_issuer/selfcheck_resource_as.py
uv run black --check tests/mcp_conformance_id_jag_issuer
uv run ruff check tests/mcp_conformance_id_jag_issuer
uv run mypy --strict tests/mcp_conformance_id_jag_issuer
uv run bandit -c pyproject.toml -iii -r tests/mcp_conformance_id_jag_issuer
uv run pytest --collect-only tests -o addopts=''
uv run pytest --collect-only tests/mcp_conformance_id_jag_issuer -o addopts=''
uv run pytest --collect-only tests/mcp_conformance_id_jag_issuer/acceptance_id_jag.py -o addopts=''
bash -n tests/mcp_conformance_id_jag_issuer/run-local.sh
```

The directory-only collection command exits 5 because zero collected tests is intentional. The static example key is test-only; the live runner overwrites it with a generated value. The primary draft files were downloaded again and their SHA-256 hashes match README.md. Consulted: [-06 §4.3.3](https://www.ietf.org/archive/id/draft-ietf-oauth-identity-assertion-authz-grant-06.txt), §4.3.4 and §4.3.4.3; the corresponding [-04 sections](https://www.ietf.org/archive/id/draft-ietf-oauth-identity-assertion-authz-grant-04.txt); [RFC 8693 §2.1, §2.2.1 and §2.2.2](https://www.rfc-editor.org/rfc/rfc8693.html#section-2.2.2).

## Proposed draft PR

**Target branch:** `providers/oauth2/id-jag` (not `main`).

**Title:** `tests: exercise ID-JAG issuance through independent MCP redemption`

**Description:**

> Adds a live, test-only acceptance check against the ID-JAG issuance branch: real login and code+PKCE, ID-JAG exchange, independent JWKS signature/claim verification and JWT-bearer redemption, then a protected MCP call. The full positive flow passes locally on `dce0a00534cb51ebe24d6a8f96ef3bc868006200`.
>
> The check intentionally remains red: 15 PASS / 6 FAIL. It exposes access-token-as-ID-Token acceptance, three invalid-subject error-code discrepancies, a multiple-audience error-code mismatch, and silent scope reduction. It pins draft-06; MCP EMA links draft-04. HANDOFF.md separates common scope/error requirements, the -04 error example ambiguity, -06 additions, and fixture policies so these results can guide implementation decisions without overstating -04 conformance failures.
>
> Validated locally with a disposable PostgreSQL database and 16 passing independent fixture self-checks; Python formatting/lint/type checks and collection checks passed. No GitHub Actions run yet. The workflow runs for PRs targeting feature branches and the suite stays outside general test discovery. No production fixes are included. Keep this draft/check non-required while the implementation and intended spec baseline are reviewed.

A draft PR against Jens's branch makes sense as an executable gap report. It should be reviewed with the stated draft baseline and known error-example ambiguity, not presented as six security vulnerabilities or a complete OAuth/MCP certification.

## Remaining coverage limits

Provisioning uses the ORM because the agent API requires an enterprise license; protocol requests use real production HTTP views. The Resource AS/MCP implementation is independent test infrastructure, not the official MCP SDK. It supports JSON Streamable HTTP, Basic client authentication, and opaque access tokens. SAML/refresh-token subjects, DPoP/mTLS-bound assertions, RAR, multi-tenant claims, and actor-token behavior remain outside this suite. Future shared MCP test infrastructure can reuse the pieces listed in README.md.
