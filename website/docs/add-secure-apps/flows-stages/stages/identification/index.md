---
title: Identification stage
---

The Identification stage is the primary user-identification step in most authentik login flows.

## Overview

This stage lets the user identify themselves by username, email address, UPN, or external source. You can also embed password entry, CAPTCHA verification, and passkey autofill directly into the identification step.

## Configuration options

- **User fields**: which identifiers the user can enter.
    - **Username**
    - **Email**
    - **UPN**
- **Password stage**: optional [Password stage](../password/index.md) to render inline instead of as a separate step.
- **Captcha stage**: optional [Captcha stage](../captcha/index.md) to run as part of identification.
- **WebAuthn Authenticator Validation stage**: optional [Authenticator Validation stage](../authenticator_validate/index.md) used for passkey autofill.
- **Case-insensitive matching**: match identifiers regardless of case.
- **Show matched user**: display the matched user's username and avatar after a valid identifier is entered.
- **Pretend user exists**: continue even when the entered identifier does not match a real user.
- **Enable remember me on this device**: allow the browser to remember the entered username and jump directly to password entry later.
- **Enrollment flow**: optional flow linked as a sign-up path.
- **Recovery flow**: optional flow linked as a recovery path.
- **Passwordless flow**: optional flow linked as a dedicated passwordless sign-in path.
- **Sources**: which OAuth or SAML sources should be shown.
- **Show source labels**: show labels in addition to source icons.

## Flow integration

This stage usually appears first in authentication and recovery flows.

- If **Password stage** is configured here, do not also bind that Password stage separately in the same flow.
- If **Captcha stage** is configured here, do not also bind that Captcha stage separately in the same flow.
- If no user fields are selected, the stage acts as a source-only entry point.

## Notes

### User fields

If no user fields are selected, only the configured sources are shown.

For **UPN**, authentik matches against the `upn` attribute on the user, which is commonly populated from an LDAP source.

### Password and CAPTCHA embedding

If you set a **Password stage** here, the password prompt appears on the same step as identification instead of as a later stage.

If you set a **Captcha stage** here, configure that CAPTCHA for invisible or background use so it renders correctly inside the identification form.

### Pretend user exists

When enabled, invalid identifiers still let the flow continue as long as the format is valid for the selected field type. Stages such as [Password](../password/index.md) and [Email](../email/index.md) are aware of this behavior and handle the synthetic pending user safely.

### Source behavior

Selected OAuth and SAML sources are shown below the local identification form. If no user fields are selected and exactly one source is configured, authentik can redirect to that source automatically as long as **Passwordless flow** is not configured.

By default, sources are shown by icon only. Enable **Show source labels** if the source name should be shown alongside the icon.

Sources can also be marked as **Promoted** in their source configuration. Promoted sources are shown as prominent full-width buttons on the login page instead of small icon buttons.

### Linked flows

The **Enrollment flow** and **Recovery flow** settings control the links shown below the identification form. The passwordless flow setting adds a direct link to a separate passwordless authentication flow.

When **Enable remember me on this device** is enabled, authentik can store the username locally and jump to the password field on later visits. Users can still select **Not you?** to enter a different username or disable the remembered value.

### Passkey autofill (WebAuthn conditional UI):ak-version[2025.12]

When configured, the Identification stage can offer passkey login directly from the browser's passkey or autofill UI without requiring the user to type a username first.

authentik automatically falls back to the normal identification flow when passkey autofill is not available.

#### Requirements

- **HTTPS** is required except on `localhost`.
- The browser must support WebAuthn conditional mediation.
- The user must have a compatible discoverable credential, also known as a resident key.
- The user must access authentik on the same hostname the passkey was created for.

#### Configuration

1. Create or edit an [Authenticator Validation stage](../authenticator_validate/index.md) that allows the **WebAuthn** device class.
2. Set the Identification stage's **WebAuthn Authenticator Validation stage** to that stage.
3. Make sure users have already enrolled a WebAuthn authenticator, for example with the [WebAuthn / FIDO2 / Passkeys Authenticator setup stage](../authenticator_webauthn/index.md).

If the user has multiple passkeys, the browser shows its own picker. In the default authentication flow, authentik skips the MFA validation stage after a passkey login with an expression policy; adjust that policy if you still want a second factor after passkey login.

#### Troubleshooting

- If no passkey prompt appears, check HTTPS, browser support, and that the validation stage is configured. The browser normally triggers the passkey suggestion when the user focuses the username field.
- If no passkey prompt appears, make sure the login page is not embedded in an iframe because some browsers block conditional UI outside top-level browsing contexts.
- If the prompt appears but falls back to username/password, check that the referenced validation stage allows WebAuthn and that the user has a valid enrolled authenticator.
