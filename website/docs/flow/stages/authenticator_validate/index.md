---
title: Authenticator Validation Stage
---

This stage validates an already configured Authenticator Device. This device has to be configured using any of the other authenticator stages:

- [Duo authenticator stage](../authenticator_duo/index.md)
- [SMS authenticator stage](../authenticator_sms/index.md).
- [Static authenticator stage](../authenticator_static/index.md).
- [TOTP authenticator stage](../authenticator_totp/index.md)
- [WebAuth authenticator stage](../authenticator_webauthn/index.md).

You can select which type of device classes are allowed.

Using the `Not configured action`, you can choose what happens when a user does not have any matching devices.

- Skip: Validation is skipped and the flow continues
- Deny: Access is denied, the flow execution ends
- Configure: This option requires a *Configuration stage* to be set. The validation stage will be marked as successful, and the configuration stage will be injected into the flow.
