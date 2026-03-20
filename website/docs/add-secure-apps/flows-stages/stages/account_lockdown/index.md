---
title: Account Lockdown stage
authentik_version: "2026.2"
authentik_enterprise: true
---

:::danger
This stage performs destructive actions on a user account. Ensure the flow includes appropriate warnings and confirmation steps before this stage executes.
:::

The Account Lockdown stage executes security lockdown actions on a target user account. For the feature overview and usage instructions, see [Account Lockdown](../../../../security/account-lockdown.md).

## Stage behavior

1. **Resolves the target account** from context (see [Target user resolution](#target-user-resolution))
2. **Applies the configured actions** to that account
3. **Creates an event** for the locked account
4. **Stores the result** in `lockdown_result`
5. **For self-service**: if sessions are deleted, redirects to completion flow (if configured) or shows the stage message

## Stage settings

| Setting                        | Description                                                   | Default                        |
| ------------------------------ | ------------------------------------------------------------- | ------------------------------ |
| **Deactivate user**            | Set `is_active` to False                                      | Enabled                        |
| **Set unusable password**      | Invalidate the password                                       | Enabled                        |
| **Delete sessions**            | Terminate all active sessions                                 | Enabled                        |
| **Revoke tokens**              | Delete all tokens (API, app password, recovery, verification) | Enabled                        |
| **Completion flow**            | Flow for self-service completion (must not require auth)      | None                           |
| **Self-service message title** | Title shown after self-service lockdown                       | "Your account has been locked" |
| **Self-service message**       | HTML message shown after self-service lockdown                | Default HTML                   |

:::warning
Disabling **Delete sessions** is not recommended as it would allow an attacker with an active session to continue using the account.
:::

## Target user resolution

The stage determines which account to lock down using this priority:

1. `lockdown_target_users` - Explicit single target supplied as a one-item list in flow context
2. `pending_user` - Current target user in the flow
3. The authenticated request user for direct self-service execution

## Flow context

### Input

| Key                     | Type       | Description                                       |
| ----------------------- | ---------- | ------------------------------------------------- |
| `lockdown_target_users` | List[User] | Explicit single target encoded as a one-item list |
| `lockdown_self_service` | bool       | `True` for self-service                           |
| `pending_user`          | User       | Current target user in the flow                   |
| `prompt_data.reason`    | str        | Reason from the Prompt stage                      |

### Output

| Key               | Type | Description              |
| ----------------- | ---- | ------------------------ |
| `lockdown_result` | dict | `{user, success, error}` |

## Self-service behavior

When `lockdown_self_service` is `True` and **Delete sessions** is enabled, the user's session is deleted during lockdown. The stage cannot continue to the next stage, so it redirects to the **Completion flow** if configured, otherwise it displays the **Self-service message** configured on the stage.

If **Delete sessions** is disabled, the flow continues normally and can show its own completion stages.

The completion flow must have **Authentication** set to **No authentication required**.

## Events

Creates a **User Lockdown Triggered** event. Use [Notification Rules](../../../../sys-mgmt/events/index.md) to send alerts.

```json
{
    "action": "user_lockdown_triggered",
    "context": {
        "reason": "User-provided reason",
        "affected_user": "username"
    }
}
```

## Usage examples

### Policy to hide results stage for self-service

```python
return not request.context.get("lockdown_self_service", False)
```

### Dynamic warning message

Prompt field with **Initial value expression** enabled:

```python
is_self_service = prompt_context.get("lockdown_self_service", False)
from django.utils.html import escape

if is_self_service:
    return """<p><strong>This will immediately:</strong></p>
    <ul>
        <li>Invalidate your password</li>
        <li>Deactivate your account</li>
        <li>Terminate all sessions</li>
        <li>Revoke all tokens</li>
    </ul>"""
else:
    targets = prompt_context.get("lockdown_target_users", [])
    target = targets[0] if targets else user
    if target:
        return f"<p><strong>Locking down:</strong></p><p><code>{escape(target.username)}</code></p>"
    return "<p><strong>Locking down the selected account.</strong></p>"
```

### Results display

Prompt field with **Initial value expression** enabled:

```python
result = prompt_context.get("lockdown_result")
from django.utils.html import escape

if not result:
    return "<p>The account has been locked down.</p>"

username = escape(result["user"].username if result.get("user") else "Unknown")
if result.get("success"):
    return f"<p><code>{username}</code> has been locked down.</p>"
return f"<p>Failed to lock down <code>{username}</code>: {escape(str(result.get('error') or 'Unknown error'))}</p>"
```

## Error handling

| Error                      | Cause                                     |
| -------------------------- | ----------------------------------------- |
| "No target user specified" | No user found in context                  |
| Failure                    | Check `lockdown_result.error` for details |
