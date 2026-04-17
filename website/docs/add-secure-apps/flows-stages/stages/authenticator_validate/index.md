---
title: Authenticator validation stage
---

The Authenticator Validation stage validates an already enrolled authenticator.

## Overview

This stage is used during authentication after a user has already enrolled one or more authenticators with a setup stage, such as:

- [Duo Authenticator Setup stage](../authenticator_duo/index.md)
- [Email Authenticator Setup stage](../authenticator_email/index.md)
- [SMS Authenticator Setup stage](../authenticator_sms/index.md)
- [Static Authenticator Setup stage](../authenticator_static/index.md)
- [TOTP Authenticator Setup stage](../authenticator_totp/index.md)
- [WebAuthn / FIDO2 / Passkeys Authenticator setup stage](../authenticator_webauthn/index.md)

## Configuration options

- **Not configured action**: control what happens when the user has no compatible authenticator.
    - **Skip**: continue the flow without MFA.
    - **Deny**: deny access and end the flow.
    - **Configure**: inject one of the configured enrollment stages and continue after that stage succeeds.
- **Configuration stages**: stages that can be injected when **Not configured action** is set to **Configure**.
- **Device classes**: which enrolled authenticator types can be used at this step.
- **Last validation threshold**: skip validation if the user has successfully used a compatible device within the configured time window.
- **WebAuthn user verification**: user-verification requirement for WebAuthn authentication.
- **WebAuthn hints**: browser hints that influence which WebAuthn authenticator is preferred.
- **WebAuthn device type restrictions**: optionally limit which WebAuthn device types are allowed.
- **Email OTP throttling factor**: exponential back-off factor for Email devices after failed verification attempts.
- **SMS OTP throttling factor**: exponential back-off factor for SMS devices after failed verification attempts.
- **TOTP throttling factor**: exponential back-off factor for TOTP devices after failed verification attempts.
- **Static OTP throttling factor**: exponential back-off factor for static recovery codes after failed verification attempts.

## Flow integration

This stage normally appears in authentication flows after [Identification](../identification/index.md) and [Password](../password/index.md), and before [User Login](../user_login/index.md).

If **Not configured action** is set to **Configure**, the stage can bootstrap enrollment by injecting one or more authenticator setup stages into the running flow.

## Notes

### Require more than one MFA method

To require users to enroll more than one MFA method and validate with each method on every login, add multiple Authenticator Validation stages to the same authentication flow.

Configure each validation stage with a different set of allowed **Device classes**, and set **Not configured action** to **Configure**.

For example, to require both TOTP and WebAuthn:

1. Create a TOTP setup stage and a WebAuthn setup stage if you do not already have them.
2. Create an Authenticator Validation stage for TOTP:
    - Set **Device classes** to `totp`.
    - Set **Not configured action** to **Configure**.
    - Set **Configuration stages** to your TOTP setup stage.
3. Create a second Authenticator Validation stage for WebAuthn:
    - Set **Device classes** to `webauthn`.
    - Set **Not configured action** to **Configure**.
    - Set **Configuration stages** to your WebAuthn setup stage.
4. Bind both validation stages to your authentication flow in the order that users should enroll and validate them.

On first sign-in, users who do not yet have one of the required methods are prompted to configure it before the flow continues. On later sign-ins, each validation stage checks only the device classes configured on that stage.

### Require at least two enrolled MFA methods of any type

If you want to require users to enroll at least two different MFA methods, regardless of which types they choose, use an [Expression Policy](../../../../customize/policies/types/expression/index.mdx) to count the enrolled device classes for the user.

```python
from authentik.stages.authenticator import devices_for_user

pending_user = request.context.get("pending_user")
if not pending_user or not pending_user.pk:
    return False

device_types = {
    device.__class__.__name__.lower().replace("device", "")
    for device in devices_for_user(pending_user, confirmed=True)
}

return len(device_types) >= 2
```

Bind the policy to the flow or stage binding that controls whether the user can continue without enrolling another authenticator.

If you select multiple **Configuration stages** on a single validation stage, users can choose which authenticator to enroll for that requirement.

### Less-frequent validation

Set **Last validation threshold** to a non-zero value to avoid prompting on every login. Any compatible authenticator within the allowed classes can satisfy that threshold.

For code-based authenticators such as TOTP, Static, and SMS, values below `seconds=30` are not useful because those authenticators do not store exact validation timestamps at sub-window precision.

### Passwordless authentication

:::caution
Firefox has known issues with some Touch ID and platform-authenticator flows. See Mozilla bug `1536482` for one longstanding example.
:::

Passwordless authentication in this stage currently relies on **WebAuthn** authenticators.

To build a dedicated passwordless flow:

1. Create an **Authentication** flow.
2. Add an Authenticator Validation stage that allows the **WebAuthn** device class.
3. Add any extra verification stages you still require.
4. End the flow with a [User Login stage](../user_login/index.md).

If you want users to choose a passkey directly from the browser's autofill UI on the identification screen, configure **Passkey autofill** in the [Identification stage](../identification/index.md#passkey-autofill-webauthn-conditional-ui). This requires a discoverable credential, also known as a resident key.

Users can either access the passwordless flow directly or reach it through an Identification stage's **Passwordless flow** link.

### WebAuthn hints

:::info
Hints are advisory and browsers can ignore them based on available authenticators or platform capabilities.
:::

Optional hints can guide the browser toward a preferred authenticator type during WebAuthn authentication:

- **Security key**: prefer a portable FIDO2 device such as a YubiKey.
- **Client device**: prefer a built-in platform authenticator such as Touch ID or Windows Hello.
- **Hybrid**: prefer a platform authenticator on a nearby mobile device, typically through a QR code.

The order of selected hints matters. For example, selecting **Security key** before **Hybrid** asks the browser to prefer security keys before hybrid authentication.

### Automatic authenticator selection

If the user has multiple compatible authenticators, authentik lets them choose one. After a successful validation, the last-used authenticator is automatically preferred the next time this stage runs.

### WebAuthn authenticator type restrictions

If you restrict allowed WebAuthn authenticator types, those restrictions only apply to WebAuthn authenticators that authentik knows how to classify. This is useful when you need to limit authentication to specific hardware families or compliance profiles.

### Throttling

To slow down brute-force attacks against code-based authentication methods, the stage applies an exponential back-off to each device after a failed verification attempt. The delay required between verification attempts grows with each successive failure:

```text
delay_seconds = factor * 2^(n - 1)
```

In this formula, `factor` is the per-device-class throttling factor configured on the stage and `n` is the number of successive failures on that device.

For example, with the default factor of `1`, the required delay between attempts is `1, 2, 4, 8, 16, ...` seconds. With a factor of `0.5`, it is `0.5, 1, 2, 4, ...` seconds. A successful verification resets the counter.

A factor of `0` disables throttling for that device class.

WebAuthn and Duo devices are not throttled.

### Authentication logging

When passwordless authentication succeeds through this stage, authentik records the method as `auth_webauthn_pwl` in flow context and related events.

Example event context:

```json
{
    "auth_method": "auth_webauthn_pwl",
    "auth_method_args": {
        "device": {
            "pk": 1,
            "app": "authentik_stages_authenticator_webauthn",
            "name": "test device",
            "model_name": "webauthndevice"
        }
    }
}
```
