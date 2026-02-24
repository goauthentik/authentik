# 2025-09 IncludeSec pentest

In September of 2025, we had a pentest conducted by [Include Security](https://includesecurity.com). This resulted in a number of code improvements to our application, though no CVEs.

> IncludeSec performed a security assessment of Authentik Security's Web Apps, APIs, Deployment Config, Servers, & ETL. The assessment team performed a 8 day effort spanning from September 4, 2025 – September 15, 2025, using a Standard Grey Box assessment methodology.

View the full report of our original [test]() and the [retest results](), completed in January/February 2026.

## Summary of findings

Below is a table summarizing the findings from the report, along with IncludeSec's risk labeling and our contextual categorization of these risks. As IncludeSec states, "It is common and encouraged that all clients recategorize findings based on their internal business risk tolerances."

| Finding | IncludeSec Risk | Status           | authentik categorization |
| ------- | --------------- | ---------------- | ------------------------ |
| H1      | High            | Risk Accepted    | None (intended)          |
| H2      | High            | Closed           | Low                      |
| H3      | High            | Risk Accepted    | None (intended)          |
| M1      | Medium          | Fixed in 2025.12 | Low                      |
| M2      | Medium          | Closed           | Low                      |
| L1      | Low             | Closed           | Low                      |
| L2      | Low             | Closed           | Low                      |
| L3      | Low             | Closed           | None (not exploitable)   |
| L4      | Low             | Closed           | Low                      |

During the time of this test, we also separately addressed a number of community-reported CVEs as reported in our security pages.

## Responses to specific findings

From the audit, this is the complete list of findings, with information about how we addressed each.

### H1: Blueprint Import Allows Arbitrary Modification of Application Objects (Internal: None)

_Issue:_ This is intended functionality. It is 'exploitable' when importing blueprints from untrusted sources without reviewing the blueprint beforehand. Flow imports are technically blueprint imports, which by design can be used to create any object within authentik.

_Improvement:_ We added a [warning banner](https://github.com/goauthentik/authentik/pull/19288) with 2025.12 to flow imports.

### H2: TOTP Brute-Force Vulnerability (Internal: Low) - Closed

_Issue:_ TOTP could in theory be brute forced for login given knowledge of a target user's password, enough time, and no WAF/altering on high amounts of requests.

_Improvement:_ We added stricter rate limiting to the infrastructure used for testing.

In addition to using authentik's built-in methods to reduce the ability for attackers to brute-force credentials, we also recommend that customers use a WAF.

### H3: Arbitrary Python Code execution (Internal: None)

_Issue:_ The authentik application allowed execution of arbitrary Python code with the same privileges as the application's system user. This behavior extended to prompt stages.

_Response:_ By design, prompt inputs can be configured to have placeholder values based on Python expressions, inheriting the behavior from expression policies. Our hardening docs already cover this as well.

### M1: Anti-Brute-Force Mechanisms Bypassed via Race conditions

_Issue:_ The anti-brute-force mechanism could be bypassed by triggering a race
condition using the default-authentication-flow given enough time and no WAF/other filtering in place.

_Improvement:_ In 2025.12, we [replaced](https://github.com/goauthentik/authentik/pull/18643) session-based login attempt retries to rely instead on the reputation scores.

Once again, in addition to using authentik's built-in methods to reduce the ability for attackers to brute-force credentials, we recommend that customers use a WAF.

### M2: Password Hashes Disclosed via Application Launch URL (Internal: Low) - Closed

_Issue:_ authentik disclosed hashes of user passwords to a privileged user when accessing a specially crafted launch URL for a custom Application.

_Fix:_ We [improved](https://github.com/goauthentik/authentik/pull/18076) the Application launch URL format.

### L1: FROM Tags in Dockerfiles Enable Supply-Chain Takeover (Internal: Low) - Closed

_Issue:_ Our container build process used Dockerfiles containing unpinned tags, allowing a possible supply chain attack from an attacker with control of
the referenced repository who could repoint the tag to a different image.

_Fix:_ We [updated](https://github.com/goauthentik/authentik/pull/17795) to use hashes for dockerfile `FROM` calls.

### L2: User Accounts Enumerable

_Issue:_ In the small test environment, the application's response time varied based on whether the supplied account was associated with a valid user, allowing potential account enumeration.

In practice, network/proxy/etc latency in a production environment would most likely make this infeasible.

_Improvement:_ We [replaced](https://github.com/goauthentik/authentik/pull/18883) a randomized call to `sleep` with `make_password`, which better emulates checking the password of a user.

### L3: [Server] Shell Command Execution Did Not Use Absolute Path (Internal: Low) - Closed

_Issue:_ authentik called openssl based on its name without specifying an absolute paths, which could lead to path hijacking.

_Fix:_ We [updated](https://github.com/goauthentik/authentik/pull/17856) to use the full path to openssl.

### L4: [Server] [Proxy] Potential Slowloris DoS (Internal: Low) - Closed

_Issue:_ The test infrastructure's HTTP server had been instantiated without setting ReadHeaderTimeout, ReadTimeout, WriteTimeout, IdleTimeout, or limiting header sizes, leaving it susceptible to Slowloris-style denial of service attacks.

_Fix:_ We [added](https://github.com/goauthentik/authentik/pull/17858) default HTTP server timeouts. We recommend that admins use a load-balancer/reverse proxy in front of authentik in production, which would have different timeout settings.

### I1: [Server] [RADIUS] RADIUS Message-Authenticator Validation

_Issue:_ RADIUS Message-Authenticator validation logic appeared to be inverted, causing valid packets to be rejected and weakening the integrity check.

RADIUS Message-Authenticator validation is the process of verifying the integrity and authenticity of a RADIUS packet using the Message-Authenticator attribute.

Although the issue is currently theoretical, correctly authenticated RADIUS messages may be rejected, causing authentication failures and a potential denial-of-service.

_Improvement:_ This was intiially [fixed](https://github.com/goauthentik/authentik/pull/17855) but later reverted; we're testing our RADIUS implementation with different clients to resolve the underlying bug that required the fix to be reverted.

## Conclusion

We encourage an open and ongoing communication with our users and community. For more information abut our security stance, read our Security Policy, Hardening authentik, and our other security-related documentation. If you have any questions or feedback you can reach us on GitHub, Discord, or via email to hello@goauthentik.io. Please follow our [security policy](https://docs.goauthentik.io/security/policy/#reporting-a-vulnerability) for reporting any security concerns or vulnerabilities.
