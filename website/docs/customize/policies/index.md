---
title: Policies
---

Policies provide customization and flexibility when defining your users' login and authentication experience.

In effect, policies determine whether or not a specific stage is applied to a flow, or whether certain users can even access the flow.

For example, you can create a policy that, for certain users, skips over a stage that prompts for MFA input. Or, you can define a policy that allows users to access a login flow only if the policy criteria are met. See below for other policies, including the reputation policy and an events-driven policy to manage notifications.

For instructions about creating and binding policies to flows and stages, refer to ["Working with policies](./working_with_policies.md)".

## Standard policies

The following policies are our standard, out-of-the box policies.

### Event-matcher policy

This policy is used by the events subsystem. You can use this policy to match events by multiple different criteria, to choose when you get notified.

### Expression Policy

See [Expression Policy](./expression.mdx).

### GeoIP policy

Use this policy for simple GeoIP lookups, such as country or ASN matching. (For a more advanced GeoIP lookup, use an [Expression policy](./expression.mdx).)

With the GeoIP policy, you can use the **Distance Settings** options to set travel "expectations" and control login attempts based on GeoIP location. The GeoIP policy calculates the values defined for travel distances (in kilometers), and then either passes or fails based on the results. If the GeoIP policy failed, the current login attempt is not allowed.

    -   **Maximum distance**: define the allowed maximum distance  between a login's initial GeoIP location and the GeoIP location of a subsequent login attempt.

    -   **Distance tolerance**: optionally, add an additional "tolerance" distance. This value is added to the **Maximum distance** value, then the total is used in the calculations that determine if the policy fails or passes.

    -   **Historical Login Count**: define the number of login events that you want to use for the distance calculations. For example, with the default value of 5, the policy will check the distance between each of the past 5 login attempts, and if any of those distances exceed the **Maximum distance** PLUS the **Distance tolerance**, then the policy will fail and the current login attempt will not be allowed.

    -   **Check impossible travel**: this option, when enabled, provides an additional layer of calculations to the policy. With Impossible travel, a built-in value of 1,000 kilometers is used as the base distance. This distance, PLUS the value defined for **Impossible travel tolerance**, is the maximum allowed distance for the policy to pass. Note that the value defined in **Historical Login Count** (the number of login events to check) is also used for Impossible travel calculations.

    -   **Impossible travel tolerance**: optionally, you can add an additional "tolerance" distance. This value is added to the built-in allowance of 1000 kilometers per hour, then the total is used in the calculations that run against each of the login events (to determine if the travel would have been possible in the amount of time since the previous login event) to determine if the policy fails or passes.

:::info
GeoIP is included in every release of authentik and does not require any additional setup for creating GeoIP policies. For information about advanced uses (configuring your own database, etc.) and system management of GeoIP data, refer to our [GeoIP documentation](../../sys-mgmt/ops/geoip.mdx).
:::

### Password-Expiry Policy

This policy can enforce regular password rotation by expiring set passwords after a finite amount of time. This forces users to set a new password.

### Password Policy

:::warning
By default, authentik's Password policy is compliant with [NIST's recommendations](https://pages.nist.gov/800-63-4/sp800-63b.html#password) for passwords. To remain compliant with NIST, be cautious when editing the default values. For additional hardening configuration settings, refer to [Hardening authentik](../../security/security-hardening.md#password-policy).
:::

This policy allows you to specify password rules, such as length and required characters.
The following rules can be set:

- Minimum amount of uppercase characters.
- Minimum amount of lowercase characters.
- Minimum amount of symbols characters.
- Minimum length.
- Symbol charset (define which characters are counted as symbols).

Starting with authentik 2022.11.0, the following checks can also be done with this policy:

- Check the password hash against the database of [Have I Been Pwned](https://haveibeenpwned.com/). Only the first 5 characters of the hashed password are transmitted, the rest is compared in authentik
- Check the password against the password complexity checker [zxcvbn](https://github.com/dropbox/zxcvbn), which detects weak password on various metrics.

### Password Uniqueness Policy

This policy prevents users from reusing their previous passwords when setting a new password. For detailed information, see [Password Uniqueness Policy](./unique_password.md).

### Reputation Policy

authentik keeps track of failed login attempts by source IP and attempted username. These values are saved as scores. Each failed login decreases the score for the client IP as well as the targeted username by 1 (one).

This policy can be used, for example, to prompt clients with a low score to pass a CAPTCHA test before they can continue.

To make sure this policy is executed correctly, set _Evaluate when stage is run_ when using it with a flow.

### Have I Been Pwned Policy

:::info
This policy is deprecated since authentik 2022.11.0, as this can be done with the password policy now.
:::

This policy checks the hashed password against the [Have I Been Pwned](https://haveibeenpwned.com/) API. This only sends the first 5 characters of the hashed password. The remaining comparison is done within authentik.
