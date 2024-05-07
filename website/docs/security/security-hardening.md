---
title: Hardening your authentik deployment
---

authentik is secure out of the box; however as everyone knows there is a consequential tradeoff between security and convenience.

With that in mind, you can take steps to further increase the security of an authentik instance by applying the steps below. All of these steps have an impact on the user experience and should only be applied knowing this tradeoff.

### Expressions

[Expressions](../property-mappings/expression.mdx) allow super-users and other highly privileged users to create custom logic within authentik to modify its behaviour. Editing/creating these expressions is, by default, limited to super-users and any related events are fully logged.

For further hardening, it is possible to prevent any user (even super-users) from using expressions to create or edit any objects. To do so, configure your deployment to block API requests to these endpoints:

-   `/api/v3/policies/expression*`
-   `/api/v3/propertymappings*`
-   `/api/v3/managed/blueprints*`

With these restrictions in place, expressions can only be edited using [Blueprints on the file system](https://docs.goauthentik.io/developer-docs/blueprints/#storage---file).

### Blueprints

Blueprints allow for templating and managing the authentik configuration as code. Just like expressions, they can only be created/edited by super-users or users with specific permissions assigned to them. However, because they interact with the authentik API on a lower level, they can create other objects.

To prevent any user from creating/editing blueprints, block API requests to this endpoint:

-   `/api/v3/managed/blueprints*`

With these restrictions in place, expressions can only be edited using Blueprints on the file system.

### CAPTCHA Stage

The CAPTCHA stage allows for additional verification of a user while authenticating or authorising an application. Because the CAPTCHA stage supports multiple different CAPTCHA providers, such as Google’s reCAPTCHA and Cloudflare’s Turnstile, the URL for the JavaScript snippet can be modified. Depending on the threat model, this could be exploited by a malicious internal actor.

To prevent any user from creating/editing CAPTCHA stages block API requests to these endpoints:

-   `/api/v3/stages/captcha*`
-   `/api/v3/managed/blueprints*`

With these restrictions in place, captcha stages can only be edited using Blueprints on the file system.
