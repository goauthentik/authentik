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

The Password Uniqueness policy prevents users from reusing their previous passwords when setting a new password. To use this feature, you will need to create a Password Uniqueness policy, using the instructions below.

## How it works

This policy maintains a record of previously used passwords for each user. When a new password is created, it is compared against this historical log. If a match is found with any previous password, the policy is not met, and the user is required to choose a different password.

The password history is maintained automatically when this policy is in use. Old password hashes are stored securely in authentik's database.

:::info
This policy takes effect after the first password change following policy activation. Before that first change, there's no password history data to compare against.
:::

## Configuration options

The Password Uniqueness Policy has two configuration options:

- **Password Field**: Enter the name of the input field to check for the new password. By default, if no custom flows are used, the field name is `password`. This field name must match the field name used in your Prompt stage.

- **Number of Historical Passwords**: This setting determines how many previous passwords are checked and stored for each user, with a default of 1. For instance, if set to 3, users will not be able to reuse any of their last 3 passwords.

## Integration with other policies

For comprehensive password security, consider using this policy alongside:

- [Password Policy](./index.md#password-policy) - To enforce password complexity rules
- [Password-Expiry Policy](./index.md#password-expiry-policy) - To enforce regular password rotation

## Implement a Password Uniqueness policy

To implement a policy that prevents users from reusing their previous passwords, follow these steps:

1. In the Admin interface, navigate to **Customization** > **Policies**.
2. Click **Create** to define a new Password Uniqueness Policy.
    - **Name**: provide a descriptive name for the policy.
    - **Password field**: enter the name of the input field to check for the new password. By default, if no custom flows are used, the field name is `password`. This field name must match the field name used in your Prompt stage.
    - **Number of previous passwords to check**: enter the number of past passwords that you want to set as the number of previous passwords that are checked and stored for each user, with a default of 1. For instance, if set to 3, users will not be able to reuse any of their last 3 passwords.
3. Bind the policy to your **password prompt stage**

:::info
Password history records are stored securely and cannot be used to reconstruct original passwords.
:::
