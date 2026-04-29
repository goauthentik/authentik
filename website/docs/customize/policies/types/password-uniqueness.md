---
title: Password Uniqueness Policy
sidebar_label: Password Uniqueness Policy
tags:
    - policy
    - password
    - security
    - enterprise
authentik_version: "2025.4.0"
authentik_enterprise: true
---

The Password Uniqueness policy is an enterprise policy that prevents users from reusing previously used passwords.

In most deployments, you attach it to a [Prompt stage](../../../add-secure-apps/flows-stages/stages/prompt/index.md) through that stage's **Validation Policies** so authentik can validate the new password at the moment it is entered.

## How it works

This policy stores a history of previous password hashes for each user. When a new password is submitted, authentik compares it against the most recent password-history entries configured in the policy.

If the new password matches one of those historical entries, the policy fails and the user must choose a different password.

Password history is maintained automatically while the policy is in use.

:::info Password History Start
This policy only starts building password history once it is in use. The first password change after you enable it seeds the history; there is no older password history to compare against before that point.
:::

## When to use it

Use Password Uniqueness when you need password-history enforcement, such as:

- security baselines that forbid password reuse
- password rotation requirements
- compliance frameworks that require password history checks

For broader password controls, combine it with:

- [Password Policy](./password.md) for complexity, HIBP, and zxcvbn checks
- [Password Expiry Policy](./password-expiry.md) if you also require password rotation

## Create the policy

To create a Password Uniqueness policy:

1. In the Admin interface, navigate to **Customization** > **Policies**.
2. Click **New Policy** to define a new Password Uniqueness Policy.
3. Configure the policy:
    - **Name**: use a descriptive name.
    - **Password field**: enter the field key that contains the new password. In the default flows this is usually `password`.
    - **Number of previous passwords to check**: choose how many previous passwords authentik should compare against and retain for future checks.
4. Click **Create Policy**.

## Attach the policy to password entry

In most cases, bind the policy to the prompt stage where the user enters the new password.

For example, if you use the `default-password-change` flow:

1. Open the `default-password-change-prompt` stage.
2. In **Validation Policies**, add your Password Uniqueness policy.
3. Save the stage.

This is the recommended placement because the policy needs access to the password field in prompt data. If you bind the policy somewhere else, that password field must still be present in the policy context.

:::info Storage Model
Password history records are stored securely and cannot be used to reconstruct original passwords.
:::

## Configuration tips

- The **Password field** must match the prompt field's **Field key** exactly.
- If you have multiple password-entry prompts, point the policy at the field that represents the new password.
- Increase the history count only as far as your requirements need. Higher values mean more password history is retained per user.
