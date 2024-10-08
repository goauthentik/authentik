---
title: Policies
---

Policies provide customization and flexibility when defining your users' login and authentication experience.

In effect, policies determine whether or not a specific stage is applied to a flow, or whether certain users can even access the flow.

For example, you can create a policy that, for certain users, skips over a stage that prompts for MFA input. Or, you can define a policy that allows users to access a login flow only if the policy criteria are met. See below for other policies, including the reputation policy and an events-driven policy to manage notifications.

For instructions about creating and binding policies to flows and stages, refer to ["Working with policies](docs/policies/working_with_policies/working_with_policies.md)".

## Standard policies

The following policies are our standard, out-of-the box policies.

### Event-matcher policy

This policy is used by the events subsystem. You can use this policy to match events by multiple different criteria, to choose when you get notified.

### Expression Policy

See [Expression Policy](expression.mdx).

### GeoIP policy

Use this policy for simple GeoIP lookups, such as country or ASN matching. (For a more advanced GeoIP lookup, use an [Expression policy](expression.mdx).)

### Password-Expiry Policy

This policy can enforce regular password rotation by expiring set passwords after a finite amount of time. This forces users to set a new password.

### Password Policy

This policy allows you to specify password rules, such as length and required characters.
The following rules can be set:

-   Minimum amount of uppercase characters.
-   Minimum amount of lowercase characters.
-   Minimum amount of symbols characters.
-   Minimum length.
-   Symbol charset (define which characters are counted as symbols).

Starting with authentik 2022.11.0, the following checks can also be done with this policy:

-   Check the password hash against the database of [Have I Been Pwned](https://haveibeenpwned.com/). Only the first 5 characters of the hashed password are transmitted, the rest is compared in authentik
-   Check the password against the password complexity checker [zxcvbn](https://github.com/dropbox/zxcvbn), which detects weak password on various metrics.

### Reputation Policy

authentik keeps track of failed login attempts by source IP and attempted username. These values are saved as scores. Each failed login decreases the score for the client IP as well as the targeted username by 1 (one).

This policy can be used, for example, to prompt clients with a low score to pass a CAPTCHA test before they can continue.

To make sure this policy is executed correctly, set _Evaluate when stage is run_ when using it with a flow.

### Have I Been Pwned Policy

:::info
This policy is deprecated since authentik 2022.11.0, as this can be done with the password policy now.
:::

This policy checks the hashed password against the [Have I Been Pwned](https://haveibeenpwned.com/) API. This only sends the first 5 characters of the hashed password. The remaining comparison is done within authentik.
