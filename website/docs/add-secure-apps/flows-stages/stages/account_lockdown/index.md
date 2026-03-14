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

1. **Resolves target users** from context (see [Target user resolution](#target-user-resolution))
2. **For each user**, performs configured actions
3. **Creates an event** for each user locked down
4. **Stores results** in `lockdown_results` context variable
5. **For self-service**: redirects to completion flow (if configured) or login page

## Stage settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Deactivate user** | Set `is_active` to False | Enabled |
| **Set unusable password** | Invalidate the password | Enabled |
| **Delete sessions** | Terminate all active sessions | Enabled |
| **Revoke tokens** | Delete all API tokens and app passwords | Enabled |
| **Completion flow** | Flow for self-service completion (must not require auth) | None |

:::warning
Disabling **Delete sessions** is not recommended as it would allow an attacker with an active session to continue using the account.
:::

## Target user resolution

The stage determines which user(s) to lock down using this priority:

1. `lockdown_target_users` - List of Users (bulk lockdown)
2. `lockdown_target_user` - Single User (admin lockdown)
3. `pending_user` - Current user in flow (self-service)

## Flow context

### Input

| Key | Type | Description |
|-----|------|-------------|
| `lockdown_target_user` | User | Single target (admin) |
| `lockdown_target_users` | List[User] | Multiple targets (bulk) |
| `lockdown_self_service` | bool | `True` for self-service |
| `pending_user` | User | Current user in flow |
| `prompt_data.reason` | str | Reason from Prompt stage |

### Output

| Key | Type | Description |
|-----|------|-------------|
| `lockdown_results` | List[dict] | `{user, success, error}` per user |

## Self-service behavior

When `lockdown_self_service` is `True`, the user's session is deleted during lockdown. The stage cannot continue to the next stage, so it redirects to the **Completion flow** if configured, otherwise to the login page.

The completion flow must have **Authentication** set to **No authentication required**.

## Events

Creates an **Account Lockdown Triggered** event per user:

```json
{
    "action": "account_lockdown_triggered",
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
    if not targets:
        target = prompt_context.get("lockdown_target_user")
        if target:
            targets = [target]
    user_list = "".join(f"<li><code>{u.username}</code></li>" for u in targets)
    return f"<p><strong>Locking down:</strong></p><ul>{user_list}</ul>"
```

### Results display

Prompt field with **Initial value expression** enabled:

```python
results = prompt_context.get("lockdown_results", [])
lines = []
for r in results:
    username = r["user"].username if r.get("user") else "Unknown"
    status = "Locked" if r.get("success") else f"Failed: {r.get('error')}"
    lines.append(f"<li><code>{username}</code> - {status}</li>")
return f"<ul>{''.join(lines)}</ul>"
```

## Error handling

| Error | Cause |
|-------|-------|
| "No target user specified" | No user found in context |
| Per-user failure | Check `lockdown_results` for error details |

Failed lockdowns for individual users do not stop processing of other users.
