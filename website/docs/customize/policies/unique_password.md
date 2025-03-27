---
title: Unique Password Policy
sidebar_label: Unique Password Policy
support_level: authentik
tags:
    - policy
    - password
    - security
    - enterprise
authentik_version: "2025.4.0"
authentik_enterprise: true
---

The Unique Password Policy prevents users from reusing their previous passwords when setting a new password.

## How it works

This policy stores a history of user passwords and checks any new password against this history. If a match is found with a previous password, the policy fails and the user is required to choose a different password.

The password history is maintained automatically when this policy is in use. Old password hashes are stored securely in authentik's database.

## Configuration options

The Unique Password Policy has two configuration options:

- **Password Field**: The field key to check for the new password. Default is `password`. This should match the field name used in your Prompt stage.

- **Number of Historical Passwords**: The number of previous passwords to check against. Default is 1. This also controls how many old passwords the system stores for each user.

  For example, setting this to 3 ensures a user cannot reuse any of their last 3 passwords.

## Usage recommendations

This policy is ideal for:

- Enforcing password rotation policies
- Improving security by preventing password reuse
- Meeting compliance requirements that mandate unique passwords

For best results, bind this policy to:

1. A Prompt stage that handles password changes
2. Password reset flows

## Integration with other policies

For comprehensive password security, consider using this policy alongside:

- [Password Policy](./index.md#password-policy) - To enforce password complexity rules
- [Password-Expiry Policy](./index.md#password-expiry-policy) - To enforce regular password rotation

## Implementation example

To implement a policy that prevents users from reusing their last 3 passwords:

1. Create a Unique Password Policy
2. Set "Number of Historical Passwords" to 3
3. Bind the policy to your password prompt stage
