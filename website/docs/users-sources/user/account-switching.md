---
title: Account switching
---

authentik can keep multiple accounts signed in within the same browser and let users switch between them from the User interface header.

## How it works

Every login creates its own session. authentik groups the sessions created by the same browser using an opaque browser cookie (`authentik_accounts`), so only that browser can switch between them. Only the most recent login is active at a time; switching to another account authenticates that account through a flow, it never silently reuses the previous session.

When a user picks another account from the switcher, authentik checks that the browser holds a live session for that account and starts the configured account switch flow with the following flow context:

- `pending_user`: the account being switched to
- `account_switch_from_user`: the account that was active when the switch started
- `is_account_switch`: set to `true`

The previous account's session stays signed in as a switch target, but its session cookie can no longer be used to act as that account.

Logins performed through a switch are recorded in the event log with `is_account_switch` and the user that switched.

## Configuration

Account switches authenticate through the brand's **Account switch flow** (under **System** > **Brands**, in the brand's **Default flows**). Any authentication flow can be used; if no flow is set, the default authentication flow is used.

The default authentication flow skips its identification stage during account switches (the account being switched to is already identified by its session), while password and authenticator validation still run. This is expressed by the `default-authentication-flow-identification-stage` expression policy bound to the identification stage:

```python
return not request.context.get("is_account_switch", False)
```

Custom flows control this the same way: bind a policy like the one above to the identification, password, or authenticator validation stage bindings, depending on what a switch back to a signed-in account needs to confirm. The flow context above is available on the policy request. Without such policies the flow runs in full, with the username of the account being switched to pre-filled.
