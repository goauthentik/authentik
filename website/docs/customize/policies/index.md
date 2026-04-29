---
title: Policies
tags:
    - policy
    - security
    - access-control
---

Policies are reusable checks in authentik. They let you control whether a user can access an application, whether a stage in a flow should run, whether a source can be used, or whether data entered in a prompt stage is valid.

If you are new to policies, start here:

- [Working with policies](./working_with_policies.md) shows how to create a policy and bind it to a flow, stage, application, or source.
- [Policy bindings and evaluation](./bindings.md) explains where policies are attached and how authentik combines the results.
- [Types of policies in authentik](./types/index.mdx) groups the built-in policy types by use case.
- [Expression policies](./types/expression/index.mdx) covers Python-based policies for custom logic.

## How policies fit together

Every policy setup has three parts:

1. A **policy** defines a single check, such as "is the client in an allowed country?" or "did the user enter an acceptable password?"
2. A **binding** decides where that policy applies, such as a flow, stage binding, application, or source.
3. The **target object** combines all of its bindings using either `Any` or `All` mode.

You can also bind a **user** or **group** directly in the same places where you bind policies. Those direct bindings are evaluated like simple allow or deny checks and do not require writing a policy.

## Choose a policy type

Use the built-in policy types when they already match what you need. Reach for an expression policy when the built-in types are too limited.

| Policy type                                           | Use it when                                                                               | Notes                                                                                                               |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| [Event Matcher](./types/event-matcher.md)             | You want to react to specific authentik events, usually for notifications or automations. | Matches event action, app, model, and client IP. See [Notifications](../../sys-mgmt/events/notifications.md).       |
| [Expression](./types/expression/index.mdx)            | You need custom logic that is not covered by a more specialized policy type.              | Most flexible option. Runs Python and can inspect flow context, prompt data, user data, request metadata, and more. |
| [GeoIP](./types/geoip.md)                             | You want to allow or deny requests based on country, ASN, or travel patterns.             | Can also check recent login distance and impossible-travel scenarios.                                               |
| [Password](./types/password.md)                       | You want to validate password complexity, HIBP exposure, or zxcvbn strength.              | Commonly attached to a prompt stage's **Validation Policies**.                                                      |
| [Password Expiry](./types/password-expiry.md)         | You want to expire passwords after a fixed number of days.                                | Can either deny login or mark the password unusable so the user must update it.                                     |
| [Password Uniqueness](./types/password-uniqueness.md) | You want to prevent password reuse.                                                       | Enterprise feature.                                                                                                 |
| [Reputation](./types/reputation.md)                   | You want to react to failed logins or suspicious sign-in activity.                        | Useful for showing CAPTCHA or another challenge only to low-reputation requests.                                    |

## Deprecated policy types

### Have I Been Pwned policy

The standalone Have I Been Pwned policy is deprecated. Use the [Password Policy](./types/password.md) instead, which includes the same HIBP check.
