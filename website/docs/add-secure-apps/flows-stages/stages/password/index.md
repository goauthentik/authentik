---
title: Password stage
---

This is a generic password prompt that authenticates the current `pending_user`. This stage allows the selection of how the user's credentials are accessed, with either a standard password, an App password, or source (LDAP or Kerberos) against which the user is authenticated.

## Create a Password stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages > Stages** and click **Create**.
3. In the **New Stage** dialog select **Password stage**, and then click **Next**.
4. Provide the following settings:

- **Name**: enter a descriptive name.
- **Stage-specific settings**:
    - **Backends**: select one or more of the following options:
        - **User database + standard password**: configures the stage to use the authentik database, accessed with the credentials and standard password of the user who is logging in.
        - **User database + app passwords**: configures the stage to use the authentik database, accessed with the user's credentials and an [App password] (created by the user, on the User interface).
        - **User database + LDAP password**: configures the stage to use the authentik database, accessed with the user identifier (User ID) and the password provided by the [LDAP source](../../../../users-sources/sources/protocols/ldap/index.md).
        - **User database + Kerberos password**: configures the stage to use the authentik database, accessed with the user identifier (User ID) and the password provided by the [Kerberos source](../../../../users-sources/sources/protocols/kerberos/index.md).
          If you select multiple backend settings, authentik goes through them each in order.
- **Configuration flow**: you are able to select any of the default flows, but the only one of the defaults that makes sense is the “default-password-change (Change Password)” one. However, you might have created a custom flow for passwords, that adds a stage for MFA or some such, so you could select that flow here instead.
- **Failed attempts before cancel**: indicate how many times a user is allowed to attempt the password.
- **Allow Show Password**: toggle this option to allow the user to view in plain text the password that they are entering.

5. Click **Finish** to create the new Password stage.

:::tip
If you create a service account, that account is auto-assigned a password, which is the equivalent of an App password. If you impersonate the service account, you can view it under the **Tokens and App passwords** section on the [User interface].
:::

## Passwordless login

There are two different ways to configure passwordless authentication;

- allow users to directly authenticate with their authenticator (only supported for WebAuthn devices), by following [these instructions](../authenticator_validate/index.mdx#passwordless-authentication).
- dynamically skip the Password stage (depending on the user's device), as documented on this page, below.

If you want users to be able to pick a passkey from the browser's passkey/autofill UI without entering a username first, configure **Passkey autofill (WebAuthn conditional UI)** in the [Identification stage](../identification/index.mdx#passkey-autofill-webauthn-conditional-ui). This is separate from configuring a dedicated passwordless flow, and can be used alongside normal identification flows.

Depending on what kind of device you want to require the user to have:

#### WebAuthn

```python
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
return WebAuthnDevice.objects.filter(user=request.context['pending_user'], confirmed=True).exists()
```

#### Duo

```python
from authentik.stages.authenticator_duo.models import DuoDevice
return DuoDevice.objects.filter(user=request.context['pending_user'], confirmed=True).exists()
```

Afterwards, bind the policy you've created to the stage binding of the password stage.

Make sure to uncheck _Evaluate when flow is planned_ and check _Evaluate when stage is run_, otherwise an invalid result will be cached.
