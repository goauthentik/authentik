---
title: Password Expiry Policy
tags:
    - policy
    - password
    - security
---

Use a Password Expiry policy when passwords should expire after a fixed number of days.

## How it works

This policy checks how many days have passed since the user's password was last changed.

When the configured limit is exceeded, the policy fails. Depending on the policy settings, authentik can either:

- deny access with an expiry message
- mark the password unusable so the user must set a new one

## Key setting

- **Days**: how old a password may be before the policy fails
- **Deny only**: if enabled, the policy only fails; if disabled, authentik can also mark the password unusable

## Create a Password Expiry policy

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **New Policy** and select **Password Expiry Policy**.
4. Configure the allowed password age and whether the policy should run in deny-only mode.
5. Click **Create Policy**.

## Common use

Password Expiry policies are usually used together with a password change or recovery flow so users have a clear path to set a new password after expiry.

If you also need password-history enforcement, combine this policy with [Password Uniqueness Policy](./password-uniqueness.md).
