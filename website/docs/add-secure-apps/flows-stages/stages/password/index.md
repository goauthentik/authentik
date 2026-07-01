---
title: Password stage
---

The Password stage prompts the current `pending_user` for a password and validates it against one or more configured backends.

## Overview

Use this stage in authentication or password-change flows when a user should prove possession of a password.

The stage supports authentik's built-in password database, app passwords, LDAP-backed passwords, and Kerberos-backed passwords.

## Configuration options

- **Backends**: select one or more password backends to test in order.
    - **User database + standard password**
    - **User database + app passwords**
    - **User database + LDAP password**
    - **User database + Kerberos password**
- **Failed attempts before cancel**: how many failed password submissions are allowed before the flow is canceled.
- **Failed attempts before lockout**: how many failed password submissions are allowed before the pending user's account is deactivated. Set this to `0` to disable account lockout.
- **Allow show password**: show a button that reveals the entered password.
- **Configuration flow**: optional authenticated flow that lets users configure or change their password from user settings.

## Flow integration

This stage is typically bound after an [Identification](../identification/index.md) stage and before an [Authenticator Validation](../authenticator_validate/index.md) or [User Login](../user_login/index.md) stage.

If the [Identification stage](../identification/index.md) has its **Password stage** option set, the password prompt is rendered as part of the identification step and the Password stage should not also be bound separately in the same flow.

### Failed attempts and account lockout

The Password stage measures failed password submissions by comparing the pending user's reputation score when the password challenge is shown with the score after each failed password submission. Each invalid password submission lowers the user's reputation score.

When **Failed attempts before lockout** is greater than `0`, authentik deactivates the pending user after the configured reputation score decrease is reached. The user must be reactivated by an administrator before they can log in again.

Configure **Failed attempts before lockout** to be less than or equal to **Failed attempts before cancel**. If **Failed attempts before cancel** is lower, the flow is canceled before the lockout threshold is reached.

The effective maximum is also bounded by the brand reputation lower limit. For example, with the default lower limit of `-5`, a user whose reputation is already `-4` can only lose one more reputation point before the score reaches the lower limit. In that case, a lockout threshold greater than `1` cannot be reached in that flow run.

## Notes

:::tip
Service accounts have automatically generated app passwords. Those can be viewed from the service account's user settings or from the admin interface.
:::

### Passwordless patterns

There are two common ways to avoid prompting for a password:

- Use an [Authenticator Validation](../authenticator_validate/index.md#passwordless-authentication) stage with WebAuthn for a dedicated passwordless flow.
- Conditionally skip the Password stage by binding a policy to its stage binding.

If you want users to be able to pick a passkey from the browser's passkey/autofill UI without entering a username first, configure **Passkey autofill (WebAuthn conditional UI)** in the [Identification stage](../identification/index.md#passkey-autofill-webauthn-conditional-ui). This is separate from configuring a dedicated passwordless flow, and can be used alongside normal identification flows.

### Dynamically skip a Password stage

This setup keeps a normal identification flow, but skips the Password stage for users who already have a supported authenticator configured.

To configure this setup:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies** and create an [Expression Policy](../../../../customize/policies/types/expression/index.mdx).
3. Configure the expression so that it returns `True` only when the Password stage should run. Use one of the expressions below, depending on the authenticator type.
4. Navigate to **Flows and Stages** > **Flows** and open your authentication flow.
5. Open the **Stage Bindings** tab, expand the Password stage binding, and bind the Expression Policy there. Do not bind it to the flow itself or directly to the stage object. For more background, see [Bind a policy to a stage binding](../../../../customize/policies/working_with_policies.md#bind-a-policy-to-a-stage-binding).
6. On the Password stage binding, enable **Evaluate when stage is run**. Disable **Evaluate when flow is planned** unless the user is already known before the flow starts. See [Planning and stage policies](../../flow/planner.md#planning-and-stage-policies).

#### WebAuthn

```python
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice

pending_user = request.context.get("pending_user")
if not pending_user:
    return True

return not WebAuthnDevice.objects.filter(user=pending_user, confirmed=True).exists()
```

Or for Duo:

```python
from authentik.stages.authenticator_duo.models import DuoDevice

pending_user = request.context.get("pending_user")
if not pending_user:
    return True

return not DuoDevice.objects.filter(user=pending_user, confirmed=True).exists()
```

Because the expression already returns whether the Password stage should run, you do not need to enable **Negate result** on the policy binding.

If the Password stage binding has more than one policy attached, review its **Policy engine mode** carefully:

- With only this policy attached, either mode works.
- If multiple policies are attached, `all` requires every policy to pass before the Password stage runs.
- If multiple policies are attached, `any` runs the Password stage when any bound policy passes.

#### Default authentication flow

The built-in `default-authentication-flow` already includes a policy binding on its Password stage, `default-authentication-flow-password-stage`, which controls whether the Password stage should appear.

If you add a second policy to that same Password stage binding, set the stage binding's **Policy engine mode** to `all` so both the built-in policy and your Expression Policy must pass before the Password stage runs.

Keep **Evaluate when stage is run** enabled on that binding. In the default blueprint, this is already configured.
