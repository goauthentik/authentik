---
title: Duo authenticator setup stage
---

The Duo Authenticator Setup stage enrolls a Duo authenticator for the current user.

## Overview

This stage connects authentik to Duo and stores a Duo-backed authenticator for the user. Duo can then be used with the [Authenticator Validation stage](../authenticator_validate/index.md).

## Configuration options

- **API hostname**: the Duo API hostname for your tenant.
- **Client ID**: Duo Auth API client identifier.
- **Client secret**: Duo Auth API secret.
- **Admin integration key**: optional Duo Admin API integration key, used for importing existing Duo users and authenticators.
- **Admin secret key**: optional Duo Admin API secret, used together with the admin integration key.
- **Authenticator type name**: optional friendly name shown to the user in self-service settings.
- **Configuration flow**: optional authenticated flow that lets users enroll this authenticator from user settings.

## Flow integration

Use this stage in an enrollment or user-settings flow where the user should enroll Duo.

To require Duo during authentication, add an [Authenticator Validation stage](../authenticator_validate/index.md) to the login flow and allow the **Duo** device class.

## Notes

- Duo authenticators created through this stage are tied to the stage because authentik needs that stage's API credentials during authentication.
- Deleting the stage also removes the Duo authenticators associated with it.

### Import existing Duo authenticators

:::info
Due to the way the Duo API works, authentik can only automatically import existing Duo users when a Duo MFA or higher license is active.
:::

If you already have Duo users, you can import their authenticators into authentik from the admin UI. The Duo username can be found in the Duo Admin dashboard under **Users**. If needed, you can also use the Duo user ID shown in the Duo Admin URL for that user.

For direct API use, the import endpoint accepts:

- `duo_user_id`: the Duo user's ID from the Duo admin portal
- `username`: the authentik username to assign the imported authenticator to

The `stage_uuid` in the request must be the Duo stage whose API credentials should be used.
