---
title: Hardening authentik
---

While authentik is secure out of the box, you can take steps to further increase the security of an authentik instance. As everyone knows, there is a consequential tradeoff between security and convenience. All of these hardening practices have an impact on the user experience and should only be applied knowing this tradeoff.

### Expressions

[Expressions](../customize/policies/expression.mdx) allow super-users and other highly privileged users to create custom logic within authentik to modify its behaviour. Editing/creating these expressions is, by default, limited to super-users and any related events are fully logged.

However, for further hardening, it is possible to prevent any user (even super-users) from using expressions to create or edit any objects. To do so, configure your deployment to block API requests to these endpoints:

-   `/api/v3/policies/expression*`
-   `/api/v3/propertymappings*`
-   `/api/v3/managed/blueprints*`

With these restrictions in place, expressions can only be edited using [Blueprints on the file system](../customize/blueprints/index.md#storage---file). Take care to restrict access to the file system itself.

### Blueprints

Blueprints allow for templating and managing the authentik configuration as code. Just like expressions, they can only be created/edited by super-users or users with specific permissions assigned to them. However, because they interact with the authentik API on a lower level, they can create other objects.

To prevent any user from creating/editing blueprints, block API requests to this endpoint:

-   `/api/v3/managed/blueprints*`

With these restrictions in place, Blueprints can only be edited via [the file system](../customize/blueprints/index.md#storage---file).

### CAPTCHA Stage

The CAPTCHA stage allows for additional verification of a user while authenticating or authorising an application. Because the CAPTCHA stage supports multiple different CAPTCHA providers, such as Google’s reCAPTCHA and Cloudflare’s Turnstile, the URL for the JavaScript snippet can be modified. Depending on the threat model, this could be exploited by a malicious internal actor.

To prevent any user from creating/editing CAPTCHA stages block API requests to these endpoints:

-   `/api/v3/stages/captcha*`
-   `/api/v3/managed/blueprints*`

With these restrictions in place, CAPTCHA stages can only be edited using [Blueprints on the file system](../customize/blueprints/index.md#storage---file).

### Content Security Policy (CSP)

:::caution
Setting up CSP incorrectly may result in the client not loading necessary third-party code.
:::

Content Security Policy (CSP) is a security standard that mitigates the risk of content injection vulnerabilities. authentik doesn't currently support CSP natively, so setting it up depends on your installation. We recommend using a [reverse proxy](../install-config/reverse-proxy.md) to set a CSP header.

authentik will require at least the following allowed locations:

```
default-src 'self';
style-src 'self' 'unsafe-inline';
script-src 'self' 'unsafe-inline';
img-src 'https:' 'http:' 'data:';
object-src 'none';
```

Your use case might require more allowed locations for various directives, e.g.

-   when using a CAPTCHA service
-   when using Sentry
-   when using any custom JavaScript in a prompt stage
-   when using Spotlight Sidecar for development
