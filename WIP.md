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
- [ ] **A3.** `OidcEndpoint` struct from `OpenIdConnectConfiguration` mirroring `endpoint.go`
  (embedded/browser URL rewriting). URL-rewrite tests.
- [ ] **A4.** ID-token verification: `decode_header`→`kid`, JWKS fetch (`reqwest` → `jwk::JwkSet`),
  RS256 verify; plus HS256-by-client-secret path keyed off
  `id_token_signing_alg_values_supported`. Fixture test.

### Phase B — session + cookies (needs A1)

- [ ] **B5.** `SessionData` + async `SessionStore` trait + `FsSessionStore` (JSON files,
  `session_<id>`, maxage→expiry). save/load/delete/expiry tests.
- [ ] **B6.** Extend `Application` to hold `Arc<dyn SessionStore>`, cookie signing key,
  `OidcEndpoint`, backchannel `reqwest` client; wire in `Application::new`. Compiles, no behavior
  change.
- [ ] **B7.** Add `axum-extra` cookie support; signed session-ID cookie read/issue helper with
  per-provider domain/secure/samesite/path/maxage (mirror `getStore` options).

### Phase C — auth-start + callback (shared flow; needs A2–A4, B)

- [ ] **C8.** `/outpost.goauthentik.io/start` route + `handle_auth_start`: ensure session ID, build
  state JWT, build authorize URL with `?rd=`, 302. (First user-visible behavior.)
- [ ] **C9.** `redirect_to_start` helper: store redirect in session, `InterceptHeaderAuth` 401
  path, forward_domain redirect validation (`checkRedirectParam`).
- [ ] **C10.** `handle_auth_callback`: validate state JWT + session-ID match, code exchange, verify
  ID token, extract claims, session maxage from `exp`, save, redirect to stored `rd`.

### Phase D — non-session auth paths + caching (needs A4, C)

- [ ] **D11.** Add `moka` TTL cache; `attempt_bearer_auth` (introspection POST) + cache get/save
  (`auth_bearer.go`, `auth.go`).
- [ ] **D12.** `attempt_basic_auth` (`goauthentik.io/token` username → bearer path; else
  client-credentials token POST + verify) (`auth_basic.go`).
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
