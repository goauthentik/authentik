# Proxy outpost rewrite review — Go (`proxyv2`) → Rust (`outpost/proxy`)

This document compares the original Go proxy outpost
(`internal/outpost/proxyv2`, plus the shared `internal/outpost/ak` package)
against the Rust rewrite (`src/outpost/proxy`, plus the shared `packages/ak-axum`
and `packages/ak-common` crates). It records what is **missing** from the rewrite
and what **behaves differently**, so each item can be triaged as a bug, an
intentional change, or a migration note.

Every finding cites the relevant `file:line` in both implementations. Findings are
tagged by severity:

- **[High]** — functional regression or behavior change likely to break real deployments.
- **[Medium]** — meaningful difference; security/correctness relevant in some setups.
- **[Low]** — minor difference, edge case, or cosmetic.
- **[Info]** — architectural / intentional difference worth documenting.

Overall the rewrite is **faithful and largely feature-complete**: all three proxy
modes, all four reverse-proxy integrations, the full OAuth2 code flow, token
verification, bearer/basic auth, session stores, single-logout, endpoint
rewriting, SNI, and PROXY-protocol support are present and behave like Go (see
§6). The notable gaps are a handful of items below.

## Summary

| # | Finding | Severity | Type | Status |
|---|---------|----------|------|--------|
| 2.1 | Upstream `Host` header differs in proxy mode (internal vs original) | High | Bug/regression | ✅ Resolved |
| 2.2 | Underscore-header smuggling mitigation is weaker | Medium | Bug/regression | ✅ Resolved |
| 2.3 | `forward_domain` `rd` redirect validation is more permissive | Medium | Bug/regression | Open |
| 3.1 | `X-Forwarded-*` now gated on trusted proxies | Info | Improvement | — |
| 3.2 | `intercept_header_auth` 401 path returns cleanly | Low | Improvement | — |
| 3.3 | Sign-out clears the session cookie | Low | Improvement | — |
| 4.1 | Sessions/cookies are not portable across the cutover | Medium | Migration | — |
| 4.2 | Cookie secret length enforced (≥32 bytes) | Low | Migration | — |
| 5.2 | Signature query parsing is case-sensitive | Low | Robustness | Open |

---

## 2. Behavioral differences — likely bugs / regressions

### 2.1 — [High] Upstream `Host` header differs in proxy mode — ✅ Resolved

**Go:** the reverse-proxy `Director` rewrites `r.URL` to the upstream but never
touches `r.Host` unless the user has an `ak_proxy.host_header` override
(`internal/outpost/proxyv2/application/mode_proxy.go:71-93`). `httputil.ReverseProxy`
sends `r.Host` as the upstream `Host`, so the upstream receives the **original
(external) host** by default.

**Rust:** the proxied request **removes** `Host` and lets the hyper client derive
it from the upstream URI authority (the internal host), only re-inserting a
`Host` when `host_override` is set:

```rust
// src/outpost/proxy/reverse_proxy.rs:141  ("The client sets `Host` from the URI authority.")
request.headers_mut().remove(HOST);
...
// :171-173 — only when an override is present
if let Some(host) = host_override { request.headers_mut().insert(HOST, host.parse()?); }
```

`host_override` is `ak_proxy.host_header` and only when non-empty
(`src/outpost/proxy/application/handlers/proxy.rs:58-60`). So by default the
upstream now receives the **internal host** instead of the external one.

**Impact:** high. Many upstreams depend on the original `Host` — absolute-URL and
redirect generation, cookie `Domain` scoping, virtual-host routing, and host
allowlists (e.g. Django `ALLOWED_HOSTS`) will all see the internal host. Note both
implementations still set `X-Forwarded-Host` to the original host
(Go `mode_proxy.go:73`; Rust `proxy.rs:43-47`), so apps that read that header are
unaffected, but apps that read `Host` will break or behave differently.

**Recommendation:** default the upstream `Host` to the original request host when
`ak_proxy.host_header` is empty (i.e. pass the external host as `host_override`
unless overridden), matching Go.

**Resolved (2026-06-22):** the upstream client is now built with `set_host(false)`
(`src/outpost/proxy/upstream.rs`), so it never derives `Host` from the upstream
URI authority, and `create_proxied_request` no longer strips the inbound `Host`
(`src/outpost/proxy/reverse_proxy.rs`). The upstream now receives the original
request host by default, or the `ak_proxy.host_header` override when set — matching
Go. Caveat: this relies on an inbound `Host` header, which holds for HTTP/1.1; the
listeners don't negotiate HTTP/2 (no ALPN configured). If HTTP/2 inbound is enabled
later, set `Host` explicitly from the resolved request host, since an h2 request
carries it in `:authority` rather than a `Host` header.

### 2.2 — [Medium] Underscore-header smuggling mitigation is weaker — ✅ Resolved

Both implementations try to strip client-supplied `X_authentik_*` underscore
headers so they cannot be confused with the authoritative dashed `X-authentik-*`
headers by upstreams that normalize underscores to dashes.

**Go** (`internal/outpost/proxyv2/application/mode_common.go:25-32`):

```go
for key := range h {
    ush := strings.ReplaceAll(key, "_", "-")
    if _, ok := h[ush]; !ok { h.Del(key) }
}
```

`h` holds canonicalized keys (`X-Authentik-Username`), but `ush` is a
non-canonical key (`X-authentik-username`), so the raw-map lookup almost always
misses for multi-segment names — meaning underscore headers are **deleted**. The
net effect is that smuggled `X_authentik_*` headers are removed.

**Rust** (`src/outpost/proxy/headers.rs:54-66`): `HeaderMap` lookups are
case-insensitive, so the dash-twin check succeeds whenever the dashed header
exists — and `add_upstream_headers` always sets the dashed header just before
calling this. Result: a smuggled `X_authentik_username` **survives** to the
upstream because its `x-authentik-username` twin is present.

**Impact:** defense-in-depth regression. Authentik's own dashed header is
authoritative, but the Rust version forwards the attacker-controlled underscore
variant alongside it.

**Recommendation:** strip request headers whose names contain `_` unconditionally
before injecting the authentik headers (or strip any `x_authentik_*` underscore
header regardless of a dash twin), reproducing Go's effective behavior.

**Resolved (2026-06-22):** `remove_underscore_headers`
(`src/outpost/proxy/headers.rs`) now drops every header whose name contains `_`,
regardless of a dash-named twin — matching Go's effective behavior. A smuggled
`X_authentik_username` is now removed even when the legitimate
`X-authentik-username` is present.

### 2.3 — [Medium] `forward_domain` `rd` redirect validation is more permissive

**Go** validates the `rd` redirect for `forward_domain` against the **raw** cookie
domain, including its leading dot
(`internal/outpost/proxyv2/application/oauth_state.go:62-66`):

```go
if !strings.HasSuffix(u.Hostname(), *a.proxyConfig.CookieDomain) { ... reject }
```

With cookie domain `.company.com`, `evilcompany.com` fails the suffix check
(the char before `company.com` is `l`, not `.`) and is rejected.

**Rust** strips the leading dot first
(`src/outpost/proxy/oauth.rs:50-56`):

```rust
let domain = cookie_domain?.trim_start_matches('.');
if !resolved.host_str()?.ends_with(domain) { return None; }
```

So with cookie domain `.company.com` (→ `company.com`), `evilcompany.com.ends_with("company.com")`
is `true` and the redirect is **accepted**.

**Impact:** widens the open-redirect surface for `forward_domain` (browser-only,
post-login redirect; an attacker would need a look-alike domain). Note this is
isolated to redirect *validation* — the routing/`redirect_to_start` host checks
strip the dot in both implementations (Go `oauth.go:82`, Rust `handlers/mod.rs:177`),
so they match there.

**Recommendation:** in `check_redirect_param` for `ForwardDomain`, require a
domain-boundary match — keep the leading dot (match against the raw cookie
domain), or check `host == domain || host.ends_with(&format!(".{domain}"))`.

---

## 3. Behavioral differences — intentional / improvements

These are still differences from Go and should be documented, but they look
deliberate (and mostly are net improvements).

### 3.1 — [Info] `X-Forwarded-Host` / `-For` / `Forwarded` are now gated on trusted proxies

**Go:** `web.GetHost` honors `X-Forwarded-Host` unconditionally
(`internal/utils/web/host.go`), and the reverse proxy trusts the connection's
forwarded headers.

**Rust:** the `Host` and `ClientIp` extractors only honor forwarded headers (and
the PROXY-protocol source address) when the connection originates from a CIDR in
`listen.trusted_proxy_cidrs`
(`packages/ak-axum/src/extract/{trusted_proxy,host,client_ip}.rs`). The default
CIDRs are loopback + RFC1918 + link-local (`authentik/lib/default.yml:52-57`).

**Impact:** a security improvement (prevents `X-Forwarded-Host` spoofing of app
routing). Deployment caveat: forward-auth routing and client-IP attribution
require the ingress/reverse-proxy IP to be within `trusted_proxy_cidrs`. This is
true by default for typical Docker/K8s private networking, but a proxy reaching
the outpost from a non-private address must be added explicitly, or the outpost
will fall back to the connection's `Host`/peer IP.

**Recommendation:** document the trusted-proxy requirement in the upgrade notes.

### 3.2 — [Low] `intercept_header_auth` 401 path returns cleanly

**Go** (`internal/outpost/proxyv2/application/oauth.go:67-77`) writes the
"no redirect performed" 401 page but is **missing a `return`**, then falls
through and also calls `http.Redirect`; it happens to render the 401 because the
status is already committed.

**Rust** (`src/outpost/proxy/application/handlers/mod.rs:159-169`) returns the 401
response directly. Same observable behavior, cleaner control flow.

### 3.3 — [Low] Sign-out clears the session cookie

**Go** `handleSignOut` deletes server-side sessions and redirects, but does not
expire the browser cookie
(`internal/outpost/proxyv2/application/application.go:294-312`).

**Rust** additionally removes the cookie via `jar.remove(...)`
(`src/outpost/proxy/application/handlers/mod.rs:325`). Minor improvement.

---

## 4. Migration / compatibility

### 4.1 — [Medium] Sessions and cookies are not portable across the cutover

- **Cookie signing differs.** Go uses gorilla `securecookie` with the
  provider `cookie_secret` as the raw HMAC key
  (`internal/outpost/proxyv2/application/session.go:59`). Rust uses
  `axum-extra` `SignedCookieJar` with `Key::derive_from(cookie_secret)` (HKDF
  expansion) (`src/outpost/proxy/cookie.rs:39`). Existing Go-issued cookies will
  not validate under Rust.
- **Postgres `session_key` differs.** Go prefixes the key with
  `authentik_proxy_session_` + a UUID
  (`internal/outpost/proxyv2/postgresstore/postgresstore.go:419,468`); Rust stores
  the bare UUID (`src/outpost/proxy/session/postgres.rs:55-72`).
- **Cookie name is identical** in both: `authentik_proxy_` + the first 8 hex chars
  of `sha256(client_id)` (Go `application.go:119-122`; Rust `cookie.rs:81-91`).
- The stored JSON shape is compatible (`{"claims": {...}, "redirect": ...}` with
  matching field names — Go `types/claims.go`, Rust `claims.rs`), but the
  key/signing differences mean sessions still don't carry over.

**Impact:** deploying the Rust outpost invalidates all existing proxy sessions;
users re-authenticate once. This is expected for a rewrite — call it out in the
release/upgrade notes.

### 4.2 — [Low] Cookie secret length is now enforced (≥32 bytes)

Rust rejects a provider whose `cookie_secret` is shorter than 32 bytes and skips
that application (`src/outpost/proxy/cookie.rs:35-37`). Go has no such check.
authentik-generated secrets satisfy this, so it only affects hand-crafted/legacy
configs.

---

## 5. Robustness / minor

### 5.2 — [Low] Callback/logout signature query parsing is case-sensitive

The proxy-mode `handle` dispatcher parses the signature query params into
`Option<bool>` via `FromStr` (`src/outpost/proxy/application/handlers/mod.rs:49-65`),
which only accepts lowercase `"true"`. Go uses case-insensitive
`strings.EqualFold` (`application/application.go:203-208`). authentik always emits
the canonical lowercase `true` (built in `oauth::callback_redirect_uri`), so this
only differs for non-canonical casing. (Note the Traefik/Caddy forward handlers
*do* use case-insensitive matching — `forward.rs:57-60` — so this is a small
internal inconsistency too.)

---

## 6. Confirmed parity

These were checked and match Go (behaviorally, allowing for idiomatic
differences):

- **Modes & routing:** `proxy`, `forward_single`, `forward_domain`; direct host
  match then longest cookie-domain suffix match; single-app fallback when only one
  app is configured (`handlers.rs:44-54` ↔ `handlers.go:97-105`).
- **Forward integrations:** Traefik, Caddy, nginx, Envoy URL reconstruction and
  response semantics, including nginx's allow-through for `/outpost.goauthentik.io`
  paths and 401-for-the-rest (`application/handlers/forward.rs` ↔ `mode_forward.go`).
- **Callback/logout dispatch** via `X-authentik-auth-callback` / `X-authentik-logout`
  query signatures, applied uniformly before mode routing
  (`handlers/mod.rs:67-81` ↔ the global middleware in `application.go:201-213`).
- **OAuth code flow:** state encoded as an HS256 JWT signed with `cookie_secret`,
  validated on issuer + session-id-vs-cookie (`oauth_state.rs`, `handlers/mod.rs:237-250`
  ↔ `oauth_state.go`). The **access token** is used as the JWT and stored as
  `raw_token` / `X-authentik-jwt` (`handlers/mod.rs:257-268`, `backchannel.rs:31-52`
  ↔ `oauth_callback.go:56-73`).
- **Token verification:** HS256 (client secret) or RS256 (JWKS), both validating
  issuer **and** audience (`token.rs:8-13`), with JWKS cache refreshed on an
  unknown `kid` (`auth.rs:101-120`) ↔ Go's `oidc` verifier + remote keyset.
- **Bearer & basic auth:** introspection for bearer; `client_credentials` for
  basic, with the `goauthentik.io/token` username shortcut to bearer; 60s
  auth-header cache, first-write-wins (`auth.rs`, `backchannel.rs` ↔ `auth*.go`).
- **Header injection:** identical `X-authentik-*` set, pipe-joined groups/
  entitlements, `additionalHeaders` from user attributes, and basic-auth from
  attributes with email fallback (`headers.rs` ↔ `mode_common.go`).
- **Allowlist:** `skip_path_regex` compiled per line; matched against path for
  proxy/forward_single and the full URL for forward_domain (`allowlist.rs` ↔
  `mode_common.go:141-156`).
- **Redirects:** `rd` validation for proxy/forward_single (host+port must equal
  external host) and the post-login redirect-or-external-host fallback
  (`oauth.rs`, `handlers/mod.rs:277-281` ↔ `oauth_state.go`, `utils.go`).
- **Single logout:** WS `SessionEnd` logs out by `sid`
  (`outpost/mod.rs:170-180`, `outpost/event.rs:116-119` ↔ `ws.go:10-29`); manual
  sign-out logs out by `sub` and redirects to `end_session_endpoint` with
  `id_token_hint` (`handlers/mod.rs:291-334` ↔ `application.go:294-312`).
- **OIDC endpoint rewriting** for embedded (`authentik_host`) and non-embedded
  (`AUTHENTIK_HOST_BROWSER`) outposts, including the issuer/JWKS handling and the
  backchannel `Host` override (`endpoint.rs`, `token_host` in `application/mod.rs:94-97`
  ↔ `endpoint.go`, `web.NewHostInterceptor`).
- **TLS:** SNI cert resolution per app with a self-signed default fallback
  (`mod.rs:183-197` ↔ `proxyv2.go:103-126`); upstream TLS validation toggled by
  `internal_host_ssl_validation` (`upstream.rs` ↔ `mode_proxy.go:18-22`).
- **PROXY protocol** on both plain and TLS listeners
  (`packages/ak-axum/src/{server.rs,accept/proxy_protocol.rs}` ↔ Go `proxyproto`).
- **Session stores:** filesystem (one JSON/securecookie file per session,
  `session_` prefix) and PostgreSQL (`authentik_providers_proxy_proxysession`,
  lazy expiry on load); periodic cleanup runs for the filesystem store only in
  **both** implementations (`session/filesystem.rs:140-160`,
  `mod.rs:97-104` ↔ `sessionstore/cleanup.go` wired from `filesystemstore.go`).
- **Refresh** on interval (default 5 min, min 30 s), on `TriggerUpdate`, and on
  `SIGUSR1`; 10 s heartbeat; reconnect with backoff
  (`outpost/event.rs` ↔ `ak/api_event.go`).
- **Reverse proxy** hop-header stripping, `Connection`-listed header removal,
  `X-Forwarded-For` appending, and WebSocket/`Upgrade` bidirectional bridging
  (`reverse_proxy.rs` ↔ Go `httputil.ReverseProxy`).
- **Error page**: self-contained branded HTML, with the underlying error shown
  only to superusers (`error_page.rs`, `proxy.rs:90-102` ↔ `error.go:16-32`).
- **Misconfiguration reporting** as a `ConfigurationError` event
  (`events.rs` ↔ `mode_common.go:126-139`).
