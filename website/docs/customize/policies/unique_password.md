---
title: Password Uniqueness Policy
sidebar_label: Password Uniqueness Policy
support_level: authentik
tags:
    - policy
    - password
    - security
    - enterprise
authentik_version: "2025.4.0"
authentik_enterprise: true
---

The Password Uniqueness Policy prevents users from reusing their previous passwords when setting a new password.

## How it works

This policy maintains a record of previously used passwords for each user. When a new password is created, it is compared against this historical log. If a match is found with any previous password, the policy is not met, and the user is required to choose a different password.

The password history is maintained automatically when this policy is in use. Old password hashes are stored securely in authentik's database.

:::info
This policy takes effect after the first password change following policy activation. Before that first change, there's no password history data to compare against.
:::

## Configuration options

The Password Uniqueness Policy has two configuration options:

- **Password Field**: The field key to check for the new password. Default is _password_. This should match the field name used in your Prompt stage.

- **Number of Historical Passwords**: The number of previous passwords to check against. Default is 1. This also controls how many old passwords the system stores for each user.

    For example, setting this to 3 ensures a user cannot reuse any of their last 3 passwords.

## Integration with other policies

For comprehensive password security, consider using this policy alongside:

- [Password Policy](./index.md#password-policy) - To enforce password complexity rules
- [Password-Expiry Policy](./index.md#password-expiry-policy) - To enforce regular password rotation

## Implementation example

To implement a policy that prevents users from reusing their last 3 passwords:

1. Create a **Password Uniqueness Policy**
2. Set **Number of Historical Passwords** to 3
3. Bind the policy to your **password prompt stage**

:::info
Password history records are stored securely and cannot be used to reconstruct original passwords.
:::
