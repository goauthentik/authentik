# WIP: Go → Rust proxy outpost rewrite

Porting the authentik proxy outpost from Go (`internal/outpost/proxyv2`) to Rust
(`src/outpost/proxy`). The Rust side has all *infrastructure* working, but every request handler is
`todo!()` and none of the auth machinery exists yet. We continue in **very small steps** — each
step below is meant to be one focused, compilable, testable commit.

## What's already done (Rust)

- Config loading + watch (`packages/ak-common/src/config`), TLS cert store + self-signed fallback
  (`packages/ak-common/src/tls`), generated API client (`ak-client`).
- `OutpostController` base + WebSocket event loop (`src/outpost/mod.rs`, `src/outpost/event.rs`).
- `ProxyOutpost`: provider refresh, SNI cert resolution, host→app lookup, HTTP/HTTPS startup
  (`src/outpost/proxy/mod.rs`).
- Per-provider `Application` with router wiring; query-signature dispatcher `handle()` is done
  (`src/outpost/proxy/application/mod.rs`, `.../handlers/mod.rs`).
- Stack: axum 0.8, tokio, hyper-util, reqwest + reqwest-middleware, rustls/aws-lc-rs (FIPS).

## What's stubbed / missing

- `todo!()`: `handle_auth_callback`, `handle_sign_out`, `proxy::handle`,
  `forward::{caddy,envoy,nginx,traefik}`.
- `ProxyOutpost::end_session` just logs. No `/outpost.goauthentik.io/start` route.
- No crates/code for: session store (fs + postgres), signed cookies, OAuth2/OIDC client,
  state JWT, `Claims` + header injection, bearer introspection + basic/client-credentials auth,
  TTL auth cache, allowlist regex, reverse-proxy forwarding, error pages.

## Locked-in decisions

1. **Session store: filesystem first** (JSON files in tempdir). Postgres
   (`authentik_providers_proxy_proxysession`, sqlx) deferred to a later step.
2. **JWT: `jsonwebtoken` with its `aws_lc_rs` feature** (no `ring`; keep single FIPS backend).
   Verify the feature exists at the pinned version when adding it; fall back to a hand-rolled
   HS256 + aws-lc-rs verifier only if not.
3. **Cookies: clean break** — `axum-extra` `SignedCookieJar`, signing key derived from
   `provider.cookie_secret`. Cookie carries only the opaque session ID; not byte-compatible with
   Go's gorilla `securecookie` (one-time re-login on cutover, acceptable).
4. **OIDC client: hand-rolled with `reqwest`** — form-POSTs for code exchange / introspection /
   client-credentials + a JWKS GET, mirroring the Go code. No `openidconnect`/`oauth2` crate
   (API already provides resolved endpoints; avoids discovery + browser/backchannel URL-rewrite
   friction).
5. Other crates: `moka` (async) for the 60s auth-header TTL cache; `regex` (already a workspace
   dep) for the allowlist.

## Key Go references (for parity)

- `application/oauth_state.go` — state JWT (HS256, iss `goauthentik.io/outpost/{client_id}`,
  sid/state/redirect; no exp/aud).
- `application/endpoint.go` — OIDC endpoint resolution incl. embedded browser vs backchannel host
  rewriting.
- `application/oauth_callback.go`, `oauth.go` — auth start + callback + redirect validation
  (`checkRedirectParam`).
- `application/auth.go`, `auth_bearer.go`, `auth_basic.go` — `checkAuth` order: session → cache →
  bearer → basic.
- `application/mode_common.go` — `getHeaders` (X-authentik-*), basic-auth-from-attributes,
  `IsAllowlisted`.
- `application/mode_forward.go`, `mode_proxy.go` — the four forward handlers + reverse-proxy data
  path.
- `application/session.go` — session options, backend selection, `Logout`/`LogoutSessions`.

## Incremental steps (each = one focused commit)

### Phase A — pure types & crypto primitives (unit-testable, no axum)

- [x] **A1.** `Claims` + `ProxyClaims` serde types (mirror `types/claims.go`; `groups`/
  `entitlements` default-empty `Vec<String>`, `raw_token`, `ak_proxy`). Round-trip JSON test.
  Done in `src/outpost/proxy/claims.rs` (container-level `#[serde(default)]`; 3 tests).
- [x] **A2.** Add `jsonwebtoken` (`aws_lc_rs` feature). `OAuthState` type + HS256 encode/decode
  signed with `cookie_secret`; **disable exp/aud validation**, enforce issuer. Tests: round-trip +
  issuer-mismatch rejection.
  Done in `src/outpost/proxy/oauth_state.rs`. Note: `jsonwebtoken` is **v10.4.0** (v10 redesign;
  HS256 encode/decode/`Validation` API matches v9). Added to workspace deps + `proxy` feature
  (`dep:jsonwebtoken`). Cleared `required_spec_claims` so the `exp`-less token decodes. 3 tests.
- [x] **A3.** `OidcEndpoint` struct from `OpenIdConnectConfiguration` mirroring `endpoint.go`
  (embedded/browser URL rewriting). URL-rewrite tests.
  Done in `src/outpost/proxy/endpoint.rs` as a pure `OidcEndpoint::new(oidc, authentik_host,
  host_browser, embedded)` (3 tests mirror the Go `endpoint_test.go` cases). NOTE: no
  `host_browser` field exists in the Rust config schema yet — add it when wiring into
  `Application::new` (B6).
- [x] **A4.** ID-token verification: `decode_header`→`kid`, JWKS fetch (`reqwest` → `jwk::JwkSet`),
  RS256 verify; plus HS256-by-client-secret path keyed off
  `id_token_signing_alg_values_supported`. Fixture test.
  Done in `src/outpost/proxy/token.rs`: pure `verify_hs256` / `verify_rs256` (issuer + audience
  + exp validated; sets `raw_token` and defaults `ak_proxy`). RS256 works on the `aws_lc_rs`
  backend with no extra feature. 4 fixture tests (HS256, RS256, wrong-issuer, unknown-kid).
  DEFERRED to B6/C10: the async JWKS **fetch** (reqwest GET), the HS256-vs-RS256 **selection**
  from `id_token_signing_alg_values_supported`, and JWKS caching/refresh on unknown `kid`.

### Phase B — session + cookies (needs A1)

- [x] **B5.** `SessionData` + async `SessionStore` trait + `FsSessionStore` (JSON files,
  `session_<id>`, maxage→expiry). save/load/delete/expiry tests.
  Done in `src/outpost/proxy/session/{mod,filesystem}.rs`. DESIGN CHANGE: `SessionStore` is an
  **enum** (native `async fn`, static dispatch), not a `dyn` trait — native async-fn traits
  aren't dyn-compatible and we avoid `async-trait`. Each file stores `{expires, data}` JSON and
  expiry is checked on `load` (no mtime/background-cleanup reliance). Added `tempfile` dev-dep.
  5 tests. DEFERRED: writable-path validation + periodic cleanup sweep (Go's `NewStore`/
  `CleanupManager`) — not needed for correctness given load-time expiry.
- [x] **B6.** Extend `Application` to hold the `SessionStore` (enum), cookie signing key,
  `OidcEndpoint`, backchannel `reqwest` client; wire in `Application::new`. Also add the
  `host_browser` config field (needed by `OidcEndpoint`, see A3). Compiles, no behavior change.
  Done: added `host_browser: Option<String>` to config schema (`AUTHENTIK_HOST_BROWSER`);
  `Application` now holds `endpoint: OidcEndpoint` (built from outpost `config["authentik_host"]`
  + `host_browser` + `is_embedded`) and `session_store: SessionStore` (filesystem, `temp_dir()`).
  DEFERRED to B7: cookie signing key (needs axum-extra). DEFERRED to C10/C13: backchannel
  `reqwest` client (needs Host-override) and `session_max_age` from `access_token_validity`
  (avoids an f64→int `as` cast until it's actually used).
- [x] **B7.** Add `axum-extra` cookie support; signed session-ID cookie read/issue helper with
  per-provider domain/secure/samesite/path/maxage (mirror `getStore` options).
  Done in `src/outpost/proxy/cookie.rs`: `SessionCookie` (own struct, independently testable)
  with `jar`/`read`/`build`. `axum-extra = 0.12.6` (compatible with axum 0.8.9), features
  `cookie-signed` + `cookie-key-expansion`; key via `Key::derive_from(cookie_secret)` (secret is
  a 32-char string). Cookie name `authentik_proxy_<sha256(client_id)[..4] hex>` via `aws-lc-rs`
  digest (added as direct dep, already transitive). Wired into `Application` (`session_cookie`).
  5 tests (round-trip through signing, attributes, wrong-key, short-secret, name stability).

### Phase C — auth-start + callback (shared flow; needs A2–A4, B)

- [x] **C8.** `/outpost.goauthentik.io/start` route + `handle_auth_start`: ensure session ID, build
  state JWT, build authorize URL with `?rd=`, 302. (First user-visible behavior.)
  Done: pure URL helpers in `src/outpost/proxy/oauth.rs` (`authorize_url`, `callback_redirect_uri`,
  `redirect_param`, `new_session_id` (uuid v4), signature/`rd` constants; 4 tests). `/start` route
  added; `handle_auth_start` (in `application/handlers/mod.rs`) reads/creates the session id from
  the signed cookie, builds the state JWT, 302s to the authorize URL, and sets the session cookie
  (`Application::session_max_age` from `access_token_validity`, via `from_secs_f64` to avoid an
  `as` cast). No store write at start (cookie carries the sid; callback creates the entry).
  NOTE: `rd` is taken raw here; validation (`checkRedirectParam`) lands in C9.
- [x] **C9.** `redirect_to_start` helper: store redirect in session, `InterceptHeaderAuth` 401
  path, forward_domain redirect validation (`checkRedirectParam`).
  Done: `oauth::check_redirect_param` (proxy/forward_single → must resolve to external host, bare
  path allowed; forward_domain → host must end with cookie domain), `oauth::url_join`,
  `oauth::start_url`; wired `handle_auth_start` to validate `rd` via `check_redirect_param`.
  `redirect_to_start` (in `handlers/mod.rs`) builds the 302 to `/start?rd=…` and returns 401 when
  `intercept_header_auth` + an `Authorization` header are present. NOTE: no session write —
  `SessionRedirect` is never read in Go (redirect comes from the state JWT). The 401 uses a plain
  body; templated error page deferred to G25. `redirect_to_start` is unused until Phase F. 6 new
  tests.
- [x] **C10.** `handle_auth_callback`: validate state JWT + session-ID match, code exchange, verify
  ID token, extract claims, session maxage from `exp`, save, redirect to stored `rd`.
  Done. New `src/outpost/proxy/backchannel.rs` (`exchange_code`, `fetch_jwks`) using the API's
  `ClientWithMiddleware` (added `reqwest` + `reqwest-middleware` direct deps). `Application` now
  holds `client` + `token_host` (browser host for the embedded `Host`-override on token requests).
  `handle_auth_callback`: 400 on missing cookie / invalid state / sid-mismatch / blank code; else
  exchanges the code, verifies the access token (HS256 by client secret if `HS256` in
  `id_token_signing_alg_values_supported`, else RS256 via JWKS) against `endpoint.issuer` +
  `client_id`, saves `SessionData{claims}` (maxage = `exp - now`), and 302s to `state.redirect`
  (fallback external host) with the session cookie. No unit test (pure I/O); covered by Phase C
  e2e milestone — its building blocks are already tested.

### Phase D — non-session auth paths + caching (needs A4, C)

- [x] **D11.** Add `moka` TTL cache; `attempt_bearer_auth` (introspection POST) + cache get/save
  (`auth_bearer.go`, `auth.go`).
  Done: added `moka` (future, default-features off). `Application.auth_cache:
  Cache<String, Claims>` (60s TTL, 10k cap), keyed by the `Authorization` header.
  `backchannel::introspect_token` (form POST, `active` check, `raw_token` set). New
  `src/outpost/proxy/auth.rs`: `bearer_token` (case-insensitive, tested) + `Application` methods
  `authorization_header`/`cached_claims`/`cache_claims`/`attempt_bearer_auth`. Helpers are unused
  until the `check_auth` orchestrator (D13). 1 new test.
- [x] **D12.** `attempt_basic_auth` (`goauthentik.io/token` username → bearer path; else
  client-credentials token POST + verify) (`auth_basic.go`).
  Done: `backchannel::client_credentials_token` (returns the **id_token**). `Application`
  methods `verify_token` (HS256-by-secret / RS256-via-JWKS selection — factored out and C10's
  callback refactored to use it) and `attempt_basic_auth` (`JWT_USERNAME` → bearer, else
  client-credentials + verify id token). Username/password parsing stays for `check_auth` (D13),
  so no base64 needed yet. Verify primitives already tested in `token.rs`; no new test (pure I/O).
- [ ] **D13.** Unified `check_auth`: session → cache → bearer → basic → `Option<Claims>`.

### Phase E — header injection + allowlist (needs A1)

- [ ] **E14.** `get_headers`/`add_headers` (all `X-authentik-*`, basic-auth from user attributes,
  additional headers, underscore-dedup). Unit test.
- [ ] **E15.** `UnauthenticatedRegex` allowlist (`IsAllowlisted`) — compile regexes in
  `Application::new`; mode-dependent path-vs-URL matching. Unit test.

### Phase F — modes (needs C, D, E)

- [ ] **F16.** Forward-auth URL helpers (`getTraefikForwardUrl`, `getNginxForwardUrl`) +
  `ReportMisconfiguration` (events API). Parsing tests.
- [ ] **F17.** `handle_traefik` + `handle_caddy` (shared logic): callback/logout dispatch,
  `check_auth`→headers, allowlist, else auth-start.
- [ ] **F18.** `handle_nginx` (200+headers / redirect-flag session save / 401) and `handle_envoy`
  (path-trim, host fixup).
- [ ] **F19.** Reverse-proxy data path (`mode_proxy.go`): hyper-util client → `internal_host`,
  request/response modification, backend-override/host-header, streaming, `X-Powered-By`,
  `check_auth`→headers or `redirect_to_start`.

### Phase G — logout, postgres, error pages

- [ ] **G20.** `handle_sign_out`: clear session, redirect to `end_session_endpoint`.
- [ ] **G21.** `ProxyOutpost::end_session`: per-app store `logout(sid == event.session_id)`
  (`session.go`).
- [ ] **G22.** `PgSessionStore` (sqlx) + feature-flag decision (`dep:sqlx` under `proxy` vs new
  `proxy-postgres`) + `PgPool` wiring + backend selection in config schema. DB-gated test.
- [ ] **G23.** Error-page rendering (templated 401/500) replacing bare status codes (`error.go`).

## Ordering risks / notes to carry forward

- **`AppError` is always 502** — return `Response` directly for 302/401/200 control flow; reserve
  `AppError` for genuine internal failures.
- **State JWT has no `exp`** — must disable `validate_exp`/`aud` in `jsonwebtoken::Validation`.
- **Feature flags**: `sqlx` is currently `core`-only; decide its gating before G22 so `Application`
  field types stay stable (filesystem-first keeps this off the critical path).
- **`end_session` mapping**: WS event carries `session_id`; claim field is `sid`. FS store must
  scan-and-match like Go's `Logout`.
- **Embedded backchannel Host override**: backchannel client rewrites Host while issuer/jwks use
  browser host — replicate in A3/A4.
- Tests: use `cargo t` (project convention), not `cargo test --lib`.

## Verification

- Per step: `cargo build` + `cargo t` (the new unit tests for that step). Workspace lints are
  strict (clippy pedantic/nursery + many restriction lints; `unwrap_used`/`todo`/`unimplemented` =
  warn) — keep each step clean.
- End-to-end milestone after Phase C: unauthenticated request to a proxy-mode app → 302 to the
  authorize endpoint; full login loop closes after C10. After Phase F: forward-auth
  (traefik/nginx) and reverse-proxy modes function against a running authentik core.
