---
title: Static authenticator setup stage
---

The Static Authenticator Setup stage creates one-time backup codes for a user. These codes are typically used as a fallback when the user's primary authenticator is unavailable.

## Overview

This stage enrolls a static authenticator device for the current user and generates a set of recovery codes. Each code can be used once.

Because static codes are a device class supported by the [Authenticator Validation stage](../authenticator_validate/index.md), they are usually added as a backup factor rather than the primary factor.

## Configuration options

- **Token count**: how many backup codes to generate for the user.
- **Token length**: how long each generated code should be.
- **Authenticator type name**: optional friendly name shown to the user in self-service settings.
- **Configuration flow**: optional authenticated flow that lets users enroll this authenticator from user settings.

## Flow integration

Use this stage in an enrollment or user-settings flow where the user is already authenticated or otherwise identified.

To use the generated backup codes during authentication, add an [Authenticator Validation stage](../authenticator_validate/index.md) to the login flow and allow the **Static** device class.

## Notes

- Static codes are intended as emergency or backup credentials.
- Each code is consumed after a successful use.
