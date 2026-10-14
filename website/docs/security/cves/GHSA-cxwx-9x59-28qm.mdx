# GHSA-cxwx-9x59-28qm

## Denial of Service via Malformed SAML Messages

### Summary

An unauthenticated attacker can send a specially formed SAML message that stops the worker process handling it, failing the requests that worker was serving at the time.

### Patches

authentik 2026.8.2, 2026.5.7 and 2026.2.7 fix this issue.

### Impact

**Only deployments that use SAML are affected, in both the identity provider and the source roles. No other protocol implementation is affected.**

The worker is restarted automatically. Sessions are held in the database, so they survive. While the messages continue, a share of legitimate traffic keeps failing.

### Workarounds

Requests to `/application/saml/*` and `/source/saml/*` can be blocked at the reverse proxy or load balancer level, which prevents this issue from being exploited. This disables SAML, so it is a stopgap until you can upgrade.

### For more information

If you have any questions or comments about this advisory:

- Email us at [security@goauthentik.io](mailto:security@goauthentik.io)
