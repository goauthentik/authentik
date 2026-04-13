---
title: User delete stage
---

The User Delete stage deletes the current `pending_user`.

## Overview

This stage is intended for unenrollment or account-removal flows where the user has already been verified and the flow should remove the account.

## Configuration options

This stage has no stage-specific configuration options.

## Flow integration

Use this stage near the end of an unenrollment flow after any confirmation, re-authentication, or policy checks have already happened.

## Notes

:::danger
This stage deletes the `pending_user` without showing a confirmation prompt. Make sure the flow includes the checks and confirmation steps you want before the stage runs.
:::

The deleted user is also removed from the current session.
