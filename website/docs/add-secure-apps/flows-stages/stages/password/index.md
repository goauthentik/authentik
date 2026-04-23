---
title: Password stage
---

This is a generic password prompt that authenticates the current `pending_user`. This stage allows the selection of how the user's credentials are validated, with either a standard password, an App password, or source (LDAP or Kerberos) against which the user is authenticated.

## Create a Password stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages > Stages** and click **New Stage**.
3. In the **New Stage** dialog select **Password stage**, and then click **Next**.
4. Provide the following settings:

- **Name**: enter a descriptive name.
- **Stage-specific settings**:
    - **Backends**: select one or more of the following options:
        - **User database + standard password**: configures the stage to use the authentik database, accessed with the credentials and standard password of the user who is logging in.
        - **User database + app passwords**: configures the stage to use the authentik database, accessed with the user's credentials and an App password (created by the user on the User interface, or an administrator on the Admin interface).
        - **User database + LDAP password**: configures the stage to use the authentik database, accessed with the user identifier (User ID) and the password provided by the [LDAP source](../../../../users-sources/sources/protocols/ldap/index.md).
        - **User database + Kerberos password**: configures the stage to use the authentik database, accessed with the user identifier (User ID) and the password provided by the [Kerberos source](../../../../users-sources/sources/protocols/kerberos/index.md).
          If you select multiple backend settings, authentik goes through them each in order.
- **Configuration flow**: you are able to select any of the default flows, but typically you should select `default-password-change (Change Password)`. However, you might have created a specific flow for passwords, that adds a stage for MFA or some such, so you could select that flow here instead.
- **Failed attempts before cancel**: indicate how many times a user is allowed to attempt the password.
- **Allow Show Password**: toggle this option to allow the user to view in plain text the password that they are entering.

5. Click **Finish** to create the new Password stage.

:::tip
If you create a service account, that account has an automatically generated App password. If you impersonate the service account, you can view it under the **Settings** > **Tokens and App passwords** section of the User interface or under **Directory** > **Tokens and App passwords** of the Admin interface.
:::

## Passwordless login

There are two different ways to configure passwordless authentication:

- allow users to directly authenticate with their authenticator (only supported for WebAuthn devices), by following [these instructions](../authenticator_validate/index.mdx#passwordless-authentication).
- dynamically skip a Password stage (depending on the user's device), as documented on this page.

If you want users to be able to pick a passkey from the browser's passkey/autofill UI without entering a username first, configure **Passkey autofill (WebAuthn conditional UI)** in the [Identification stage](../identification/index.mdx#passkey-autofill-webauthn-conditional-ui). This is separate from configuring a dedicated passwordless flow, and can be used alongside normal identification flows.

### Dynamically skip a Password stage

This setup keeps a normal identification flow, but skips the Password stage for users who already have a supported authenticator configured.

To configure this setup:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies** and create an [Expression Policy](../../../../customize/policies/types/expression/index.mdx).
3. Configure the expression so that it returns `True` only when the Password stage should run. Use one of the expressions below, depending on the authenticator type.
4. Navigate to **Flows and Stages** > **Flows** and open your authentication flow.
5. Open the **Stage Bindings** tab, expand the Password stage binding, and bind the Expression Policy there. Do not bind it to the flow itself or directly to the stage object. For more background, see [Bind a policy to a stage binding](../../../../customize/policies/working_with_policies.md#bind-a-policy-to-a-stage-binding).
6. On the Password stage binding, enable **Evaluate when stage is run**. Disable **Evaluate when flow is planned** unless the user is already known before the flow starts.

#### WebAuthn

```python
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice

pending_user = request.context.get("pending_user")
if not pending_user:
    return True

return not WebAuthnDevice.objects.filter(user=pending_user, confirmed=True).exists()
```

#### Duo

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
