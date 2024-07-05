---
title: WebAuthn authenticator setup stage
---

This stage configures a WebAuthn-based Authenticator. This can either be a browser, biometrics or a Security stick like a YubiKey.

### Options

#### User verification

Configure if authentik should require, prefer or discourage user verification for the authenticator. For example when using a virtual authenticator like Windows Hello, this setting controls if a PIN is required.

#### Resident key requirement

Configure if the created authenticator is stored in the encrypted memory on the device or in persistent memory. When configuring [passwordless login](../identification/index.md#passwordless-flow), this should be set to either _Preferred_ or _Required_, otherwise the authenticator cannot be used for passwordless authentication.

#### Authenticator Attachment

Configure if authentik will require either a removable device (like a YubiKey, Google Titan, etc) or a non-removable device (like Windows Hello, TouchID or password managers), or not send a requirement.

#### Device type restrictions

:::info
Requires authentik 2024.4
:::

Optionally restrict the types of devices allowed to be enrolled. This option can be used to ensure users are only able to enroll FIPS-compliant devices for example.

When no restrictions are selected, all device types are allowed.

As authentik does not know of all possible device types, it is possible to select the special option `authentik: Unknown devices` to allow unknown devices.
