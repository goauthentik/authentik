---
title: Hardening authentik
sidebar_position: 2
---

While authentik is secure out of the box, you can take steps to further increase the security of an authentik instance. As everyone knows, there is a consequential tradeoff between security and convenience. Many of these hardening practices have an impact on the user experience and should only be applied knowing this tradeoff. Apply the ones that match your threat model rather than all of them at once.

## Authentication

### Password policy

authentik's shipped password policy is a reasonable baseline: an 8-character minimum plus a zxcvbn strength check. Two changes bring it in line with the [NIST SP 800-63 Digital Identity Guidelines](https://pages.nist.gov/800-63-4/sp800-63b.html#password):

- Set the minimum password length to 15 characters. NIST allows 8 characters only where the password is one factor of MFA, and the shipped flow skips [MFA validation](../add-secure-apps/flows-stages/stages/authenticator_validate/index.md) for users with no authenticator enrolled. If MFA is mandatory in your deployment, 8 characters remains sufficient.
- Enable the **Check haveibeenpwned.com** blocklist comparison, which covers NIST's requirement to check passwords against commonly used, expected, or compromised values.

:::note
The haveibeenpwned.com check requires outbound network access, so it cannot be used on [air-gapped instances](../install-config/air-gapped.mdx). An air-gapped deployment would need an [Expression policy](../customize/policies/types/expression/index.mdx) checking against a locally held list.
:::

For further options, see [Password policy](../customize/policies/types/password.md). A [password expiry policy](../customize/policies/types/password-expiry.md) is also available, though NIST no longer recommends routine forced rotation.

### Multi-factor authentication

Requiring a second factor is the single most effective change you can make to an authentication flow. Add an [Authenticator Validation stage](../add-secure-apps/flows-stages/stages/authenticator_validate/index.md) to your authentication flow and consider the following settings:

- Set **Not configured action** to **Configure** so that users without an authenticator are required to enroll one, or to **Deny** if enrollment is handled out of band. Leaving it on **Skip** means users without a device sign in with a password alone.
- Restrict **Device Classes** to the methods you accept. Limiting the stage to WebAuthn removes phishable factors such as TOTP and SMS.
- Set **WebAuthn User verification** to require user verification, so the authenticator confirms the user's presence and identity rather than only proving possession.
- Use **WebAuthn Device type restrictions** to limit authentication to approved hardware families. Configure the same allowlist on the [WebAuthn authenticator setup stage](../add-secure-apps/flows-stages/stages/authenticator_webauthn/index.md) so that new enrollments match.

    This filter only applies to devices that have a stored device type. Devices enrolled before authentik 2024.4, and authenticators whose AAGUID is unknown, have no stored type and are not matched by the filter, so they continue to work. For an enforceable policy, remove those enrollments and have the users re-enroll.

- Lower or clear the **Last validation threshold** if you do not want authentik to skip validation for users who recently used a device.
- Keep the throttling factors at or above their defaults. They apply exponential back-off to code-based methods after failed attempts.

Recovery flows deserve the same scrutiny as authentication flows. A recovery flow that only requires an emailed link reduces the whole account to the security of the user's mailbox.

### Account enumeration

An [Identification stage](../add-secure-apps/flows-stages/stages/identification/index.md) has **Pretend user exists** enabled by default, so an unknown identifier continues through the flow instead of failing immediately. A few settings narrow what is left:

- Keep **Pretend user exists** enabled. With it off, an unknown identifier fails at this stage while a valid one continues, which tells an attacker which is which.
- Disable **Show matched user**, which is enabled by default. It displays the matched account's username and avatar on the following step, and for an unknown identifier authentik shows the value that was typed instead, so the two cases can look different.
- Limit **User Fields** to the identifiers you actually need. Accepting both username and email widens the range of values an attacker can test.
- Remove the **Enrollment flow**, **Recovery flow**, and **Passwordless flow** links from the stage if those paths should not be advertised. This only removes the link from the login screen. The flows themselves stay reachable at `/if/flow/<slug>/`, so to actually restrict them, bind a policy to the flow or delete it.

### Brute-force resistance

Combine the following controls to slow down credential-stuffing attempts:

- Use a [Reputation policy](../customize/policies/types/reputation.md) to react to repeated failed attempts from a username or client IP. The policy passes when the score is at or below its threshold, so bind it to a [CAPTCHA stage](../add-secure-apps/flows-stages/stages/captcha/index.md) to challenge low-reputation requests, or to the authentication flow with **Negate** enabled to deny them. Score limits are configurable under **System** > **Settings**.
- Add a CAPTCHA stage unconditionally, either as its own stage or configured inline on the Identification stage, if you would rather not make it reputation-dependent.
- Bind a [GeoIP policy](../customize/policies/types/geoip.md) to restrict sign-ins to expected countries or to require additional verification elsewhere.
- Configure [notification rules](../sys-mgmt/events/notifications.md) on the `login_failed` and `suspicious_request` events so that spikes are surfaced rather than only recorded.

## Sessions

### Session lifetime

The [User Login stage](../add-secure-apps/flows-stages/stages/user_login/index.md) controls how long an authenticated session lasts.

- Set **Session duration** to an explicit value rather than leaving it at `seconds=0`. A value of `seconds=0` is intended to end the session when the browser session ends, but browsers vary in how they honor this.
- Set **Remember me offset** to `seconds=0` to hide the remember-me option, or keep the offset short.
- Set **Remember device** to `seconds=0` if you do not want authentik to store a long-lived device cookie.
- Enable **Terminate other sessions** so that a new sign-in invalidates the user's existing sessions.

### Session binding

The User Login stage can also bind a session to the network and location it was created from. authentik then terminates the session when the client's network or location changes beyond the configured strictness, which limits how far a stolen session cookie can travel. A cookie replayed from within the same permitted ASN or region still works, so treat this as a way to detect relocation rather than as a guarantee against replay.

- **Network binding** can bind to ASN, ASN and network, or ASN, network, and IP.
- **GeoIP binding** can bind to continent, continent and country, or continent, country, and city.

When a binding is violated, authentik terminates the session and records a logout event describing what changed.

:::warning
Stricter bindings cause more spurious logouts. Users on mobile networks, on VPNs, or behind load-balanced egress can change ASN or IP mid-session. Start with the loosest binding that meets your requirements and review the resulting logout events before tightening it.
:::

Each binding needs its own database. Network binding uses the ASN database ([`AUTHENTIK_EVENTS__CONTEXT_PROCESSORS__ASN`](../install-config/configuration/configuration.mdx#authentik_events__context_processors__asn)), and GeoIP binding uses the GeoIP City database ([`AUTHENTIK_EVENTS__CONTEXT_PROCESSORS__GEOIP`](../install-config/configuration/configuration.mdx#authentik_events__context_processors__geoip)).

:::warning
If the database is missing, the lookup fails, the binding is treated as broken, and the session is terminated. This check only runs once a client's IP changes, not at login, so the problem can stay hidden long after the binding is enabled.
:::

## Administrative access

### Limit superusers

Any account in a group with **Superuser Privileges** enabled can change every object in authentik, including the flows that protect it. Grant the smallest set of permissions that lets an administrator do their job:

- Use [roles](../users-sources/roles/index.md) and [access control](../users-sources/access-control/index.mdx) to assign specific object and global permissions instead of superuser membership.
- Review superuser group membership regularly, and treat every superuser account as requiring phishing-resistant MFA.

### Impersonation

Impersonation lets an administrator act as another user. Under **System** > **Settings**:

- Set **Impersonation** to disabled if the feature is not needed. This applies globally, including to superusers.
- Keep **Require reason for impersonation** enabled so every use is recorded with a justification.

Impersonation always generates `impersonation_started` and `impersonation_ended` events. Configure a [notification rule](../sys-mgmt/events/notifications.md) on these so that use is visible in real time rather than only on audit.

### Tokens and app passwords

API tokens and app passwords bypass flow-based authentication, including MFA.

Review existing tokens under **Directory** > **Tokens and App passwords**, and prefer [service accounts](../users-sources/user/account-types/service-accounts.md) with scoped permissions over tokens tied to a superuser.

### Audit events

[Events](../sys-mgmt/events/index.md) are authentik's audit log. Two settings under **System** > **Settings** matter for retention:

- **Event retention** defaults to `days=365`. Increase it to match your retention requirements, or forward events to an external system and reduce it. Changing the value only affects new events.
- **GDPR compliance** deletes a user's events when the user is deleted. Disable it if your audit requirements outweigh that, keeping local data protection obligations in mind.

Notification rules on `model_created`, `model_updated`, `model_deleted`, `secret_view`, and `password_set` give early warning of changes to authentik's own configuration.

## Restricting configuration changes

Expressions, blueprints, and CAPTCHA stages let a highly privileged user change how authentik behaves. By default they are limited to superusers and users with the relevant permissions, and all changes are logged. To remove the ability entirely, block the corresponding API endpoints in front of authentik, for example at your [reverse proxy](../install-config/reverse-proxy.md).

With any of these restrictions in place, the affected objects can only be edited through [blueprints on the file system](../customize/blueprints/index.mdx#as-a-local-file). Take care to restrict access to the file system itself, and to the process that deploys files to it.

### Expressions

[Expressions](../customize/policies/types/expression/index.mdx) allow super-users and other highly privileged users to create custom logic within authentik to modify its behavior. Editing/creating these expressions is, by default, limited to super-users and any related events are fully logged.

To prevent any user, including superusers, from using expressions to create or edit objects, block:

- `/api/v3/policies/expression*`
- `/api/v3/propertymappings*`
- `/api/v3/stages/prompt/prompts*`
- `/api/v3/managed/blueprints*`

### Blueprints

Blueprints allow for templating and managing the authentik configuration as code. Just like expressions, they can only be created/edited by super-users or users with specific permissions assigned to them. However, because they interact with the authentik API on a lower level, they can create other objects.

To prevent any user from creating or editing blueprints, block:

- `/api/v3/managed/blueprints*`

### CAPTCHA Stage

The CAPTCHA stage allows for additional verification of a user while authenticating or authorizing an application. Because the CAPTCHA stage supports multiple different CAPTCHA providers, such as Google's reCAPTCHA and Cloudflare's Turnstile, the URL for the JavaScript snippet can be modified. Depending on the threat model, this could be exploited by a malicious internal actor.

To prevent any user from creating or editing CAPTCHA stages, block:

- `/api/v3/stages/captcha*`
- `/api/v3/managed/blueprints*`

## Deployment

### Secret key

[`AUTHENTIK_SECRET_KEY`](../install-config/configuration/configuration.mdx#authentik_secret_key) signs session cookies. Generate it from a cryptographically secure source, keep it out of version control, and supply it through a secret manager rather than a plaintext environment file. Changing it invalidates all active sessions, which also makes it a way to force a global logout.

### Trusted proxy headers

[`AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS`](../install-config/configuration/configuration.mdx#authentik_listen__trusted_proxy_cidrs) defines which source addresses are allowed to set proxy headers such as `X-Forwarded-For`. The default includes the private ranges, which is broad for most deployments.

Narrow it to the addresses of your actual reverse proxies. If any untrusted client can reach authentik directly from within one of the listed ranges, it can spoof its own client IP, which in turn undermines reputation policies, GeoIP policies, session binding, and the accuracy of the audit log.

### Database connections

Set [`AUTHENTIK_POSTGRESQL__SSLMODE`](../install-config/configuration/configuration.mdx#postgresql-settings) to `verify-ca`, or to `verify-full` when hostname verification is available, whenever the database is not reached over a trusted local socket. The default of `disable` performs no certificate validation.

### Cookie scope

[`AUTHENTIK_COOKIE_DOMAIN`](../install-config/configuration/configuration.mdx#authentik_cookie_domain) controls the domain the session cookie is set on. By default the cookie is scoped to the domain authentik is served from, which is the narrowest option. Only widen it to a parent domain if you need cookie sharing across subdomains, and be aware that every host under that domain then receives the cookie.

### Embedded outpost

The embedded outpost runs inside the authentik server and serves proxy provider traffic. If you run standalone outposts, or use no proxy providers at all, set `AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST` to `true` to remove that surface.

### Logging and error reporting

- Keep [`AUTHENTIK_LOG_LEVEL`](../install-config/configuration/configuration.mdx#authentik_log_level) at `info` or higher in production. The `trace` level includes session cookies and other sensitive details in logs.
- [`AUTHENTIK_ERROR_REPORTING__ENABLED`](../install-config/configuration/configuration.mdx#authentik_error_reporting) is disabled by default. If you enable it, leave `AUTHENTIK_ERROR_REPORTING__SEND_PII` disabled, or point the DSN at a Sentry instance you control.
- [`AUTHENTIK_DISABLE_UPDATE_CHECK`](../install-config/configuration/configuration.mdx#authentik_disable_update_check) stops authentik from contacting an external service. Note that disabling it also removes notifications about security releases, so plan another way to track them.

## HTTP headers

### Content Security Policy (CSP)

:::warning
Setting up CSP incorrectly might result in the client not loading necessary third-party code.
:::

:::warning
In some cases, a CSP header will already be set by authentik (for example, in [user uploaded content](https://github.com/goauthentik/authentik/pull/12092/)). Do not overwrite an already existing header as doing so might result in vulnerabilities. Instead, add a new CSP header.
:::

Content Security Policy (CSP) is a security standard that mitigates the risk of content injection vulnerabilities. authentik doesn't currently support CSP natively, so setting it up depends on your installation. We recommend using a [reverse proxy](../install-config/reverse-proxy.md) to set a CSP header.

authentik requires at least the following allowed locations:

```
default-src 'self';
img-src https: data:;
object-src 'none';
frame-ancestors 'self';              # Same-origin framing is used by some SAML endpoints
style-src 'self' 'unsafe-inline';    # Required due to Lit/ShadowDOM
script-src 'self' 'unsafe-inline';   # Required for generated scripts
```

Your use case might require more allowed locations for various directives, for example:

- when using a CAPTCHA service
- when using Sentry
- when using any custom JavaScript in a prompt stage
- when using Spotlight Sidecar for development
- when using images hosted via HTTP

:::note
`frame-ancestors 'none'` is stricter, but several SAML endpoints intentionally permit same-origin framing. Use `'self'` unless you have confirmed that no SAML provider in your deployment relies on it.
:::

### Other headers

authentik already sends `X-Frame-Options` on its own responses. At the reverse proxy, consider adding:

- `Strict-Transport-Security`, once you are confident every host under the domain is served over HTTPS.
- `Referrer-Policy: strict-origin-when-cross-origin` or stricter, so that flow URLs containing tokens are not leaked in referrers.
- `X-Content-Type-Options: nosniff`.
