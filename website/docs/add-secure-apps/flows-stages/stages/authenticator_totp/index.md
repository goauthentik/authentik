---
title: TOTP authenticator setup stage
---

The TOTP Authenticator Setup stage enrolls a time-based one-time password device for the user, such as Google Authenticator, Authy, 1Password, or similar authenticator apps.

## Overview

This stage creates a TOTP authenticator for the current user and presents a standard OTP configuration URL that authenticator apps can scan or import.

The enrolled TOTP authenticator can then be used with the [Authenticator Validation stage](../authenticator_validate/index.md).

## Configuration options

- **Digits**: choose whether generated codes use 6 or 8 digits.
- **Authenticator type name**: optional friendly name shown to the user in self-service settings.
- **Configuration flow**: optional authenticated flow that lets users enroll this authenticator from user settings.

## Flow integration

Use this stage in an enrollment or user-settings flow where the user can add a TOTP device.

To require that device during login, add an [Authenticator Validation stage](../authenticator_validate/index.md) to the authentication flow and allow the **TOTP** device class.

## Notes

- Six-digit TOTP codes are the most widely compatible option.
- During enrollment, authentik uses the active brand's title as the issuer shown in the TOTP app. If you operate multiple authentik instances with the same usernames, distinct brand titles help avoid confusion in authenticator apps.
