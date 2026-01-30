---
title: Account Lockdown stage
authentik_version: "2026.2"
authentik_enterprise: true
---

:::danger
This stage performs destructive actions on a user account. Ensure the flow includes appropriate warnings and confirmation steps before this stage executes.
:::

The Account Lockdown stage executes security lockdown actions on a target user account. It is designed to quickly secure an account that may have been compromised.

For more information about the Account Lockdown feature, see [Account Lockdown](../../../../security/account-lockdown.md).

## Actions

The stage can perform the following actions (all configurable):

| Action | Description |
|--------|-------------|
| **Deactivate user** | Sets `is_active` to False, preventing login |
| **Set unusable password** | Invalidates the user's password |
| **Delete sessions** | Terminates all active sessions for the user |
| **Revoke tokens** | Deletes all API tokens and app passwords |

## Target user

The stage determines which user(s) to lock down from the flow context:

1. `lockdown_target_users` - List of users for bulk lockdown
2. `lockdown_target_user` - Single target user
3. `pending_user` - The user currently being processed in the flow

## Flow context

The stage reads from and writes to the flow context:

### Input context

| Key | Type | Description |
|-----|------|-------------|
| `lockdown_target_user` | User | Single user to lock down |
| `lockdown_target_users` | List[User] | Multiple users for bulk lockdown |
| `lockdown_self_service` | bool | Whether this is a self-service lockdown |
| `prompt_data.reason` | str | Reason for lockdown (from a Prompt stage) |
| `lockdown_reason` | str | Alternative location for reason |

### Output context

| Key | Type | Description |
|-----|------|-------------|
| `lockdown_results` | List[dict] | Results for each user: `{user, success, error}` |

## Self-service lockdown

When `lockdown_self_service` is True in the flow context, the stage handles the lockdown differently:

1. All lockdown actions are executed
2. Since the user's session is deleted, they cannot continue in the current flow
3. The user is redirected to the **Completion flow** configured on the stage

The completion flow must have **Authentication** set to **No authentication required** since the user is no longer authenticated.

## Stage settings

| Setting | Description | Default |
|---------|-------------|---------|
| Name | Stage name | Required |
| Deactivate user | Deactivate the user account | Enabled |
| Set unusable password | Invalidate the user's password | Enabled |
| Delete sessions | Terminate all active sessions | Enabled |
| Revoke tokens | Delete all API tokens and app passwords | Enabled |
| Completion flow | Flow to redirect users to after self-service lockdown | None |

## Events

The stage creates an **Account Lockdown Triggered** event for each user locked down. The event includes:

- The reason provided for the lockdown
- The affected user's username
- The HTTP request context

These events can be used with [Notification Rules](../../../../sys-mgmt/events/index.md) to send alerts when lockdowns occur.

## Example flow structure

A typical lockdown flow includes:

1. **Prompt Stage** - Display warning message and collect reason
2. **Account Lockdown Stage** - Execute lockdown actions
3. **Prompt Stage** (admin only) - Display results

For self-service lockdowns, the completion message is shown in a separate unauthenticated flow configured on the stage.
