---
title: Account Lockdown stage
authentik_version: "2025.5.0"
authentik_enterprise: true
---

:::danger
This stage performs destructive actions on a user account. Ensure the flow includes appropriate warnings and confirmation steps before this stage executes.
:::

The Account Lockdown stage executes security lockdown actions on a target user account. For the feature overview and usage instructions, see [Account Lockdown](../../../../security/account-lockdown.md).

## Stage behavior

1. **Resolves the target account** from the flow query parameters (see [Target user resolution](#target-user-resolution))
2. **Applies the configured actions** to that account
3. **Creates an event** for the locked account
4. **For self-service**: if sessions are deleted, redirects to the completion flow

## Stage settings

| Setting                   | Description                                                                         | Default |
| ------------------------- | ----------------------------------------------------------------------------------- | ------- |
| **Deactivate user**       | Set `is_active` to False                                                            | Enabled |
| **Set unusable password** | Invalidate the local authentik password. External source passwords are not changed. | Enabled |
| **Delete sessions**       | Terminate all active sessions                                                       | Enabled |
| **Revoke tokens**         | Delete all tokens and grants (API, app password, recovery, verification, OAuth)     | Enabled |
| **Completion flow**       | Flow for self-service completion (must not require auth)                            | None    |

:::warning
Disabling **Delete sessions** is not recommended as it would allow an attacker with an active session to continue using the account.
:::

## Target user resolution

The account lockdown API pre-plans the flow with the selected user as the flow's `pending_user`. The stage uses that `pending_user` as the account to lock.

The resolved target must be:

- a real user account
- not the anonymous user
- not an internal service account

If no valid target user can be resolved, the stage returns an invalid response.

## Reason input

The stage reads the lockdown reason from:

1. `prompt_data.lockdown_reason`
2. `lockdown_reason` in the flow plan context
3. an empty string if neither is set

## Self-service behavior

When the resolved target user is the same user who is currently authenticated and **Delete sessions** is enabled, the user's session is deleted during lockdown. The stage cannot continue to the next stage, so it redirects to the **Completion flow**.

If **Delete sessions** is disabled, the flow continues normally and can show its own completion stages.

The completion flow must have **Authentication** set to **No authentication required**.

## Events

Creates a **User Write** event with an account-lockdown action ID. Use [Notification Rules](../../../../sys-mgmt/events/index.md) to send alerts. To match account-lockdown events, use action `user_write` and query `context.action_id = "account_lockdown"`.

```json
{
    "action": "user_write",
    "context": {
        "action_id": "account_lockdown",
        "reason": "User-provided reason",
        "affected_user": "username"
    }
}
```

## Usage examples

### Policy to show a completion stage only for administrator-triggered lockdowns

```python
target_user = request.context.get("pending_user")
current_user = request.http_request.user

return bool(target_user and current_user and target_user.pk != current_user.pk)
```

### Dynamic warning message

Prompt field with **Initial value expression** enabled:

```python
target = user
current_user = http_request.user
is_self_service = bool(target and current_user and target.pk == current_user.pk)
from django.utils.html import escape

if is_self_service:
    return """<p><strong>This will immediately:</strong></p>
    <ul>
        <li>Invalidate your local authentik password</li>
        <li>Deactivate your account</li>
        <li>Terminate all sessions</li>
        <li>Revoke all tokens</li>
    </ul>"""
else:
    if target:
        return f"<p><strong>Locking down:</strong></p><p><code>{escape(target.username)}</code></p>"
    return "<p><strong>Locking down the selected account.</strong></p>"
```

## Error handling

| Error                      | Cause                                   |
| -------------------------- | --------------------------------------- |
| "No target user specified" | No valid pending user found in the flow |
| Failure                    | The stage returns an invalid response   |
