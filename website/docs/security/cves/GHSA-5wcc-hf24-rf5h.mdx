# GHSA-5wcc-hf24-rf5h

_Reported by [@bugbunny-research](https://github.com/bugbunny-research)_

## Unauthenticated Access via Client-Controlled X-Original-URI Header in Nginx Forward-Auth Mode

### Summary

In nginx forward-auth mode, the authentik outpost reads the forwarded request URL from a header that nginx does not set, but that a client can freely inject. By crafting this header to point at an internal outpost path, an unauthenticated attacker can cause the outpost to return HTTP 200 — causing nginx to forward the original request to the protected backend without authentication.

### Patches

authentik 2025.12.5 and 2026.2.3 fix this issue.

### Impact

This vulnerability only affects deployments using authentik's nginx forward-auth integration. Traefik, Caddy, and proxy mode deployments are not affected.

In nginx forward-auth mode, the outpost builds the URL it evaluates from a header that nginx never sets but clients can freely inject. Because nginx's `auth_request` module forwards all client headers to the authentication subrequest, an attacker-supplied value reaches the outpost unmodified.

The outpost unconditionally allows requests whose forwarded URL path begins with `/outpost.goauthentik.io/` (to permit internal endpoints such as the OAuth callback). An attacker can set the injected header to any path under that prefix, causing the outpost to return 200 and nginx to proxy the original request to the backend as if authenticated.

The attack requires only a single HTTP header — no account, session, or prior knowledge of the target application. Any resource behind the nginx gateway is accessible: reads, writes, and deletes depending on what the backend exposes. The CVSS 3.1 score is 10.0 (Critical).

### Workarounds

Operators can mitigate this immediately at the nginx layer by explicitly clearing the `X-Original-URI` header in the nginx location block that proxies traffic to the outpost. This prevents the attacker-supplied value from reaching the outpost regardless of the application-level logic. Refer to the nginx documentation for `proxy_set_header` to clear individual headers.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
