---
title: Account switching
---

authentik can keep multiple accounts signed in within the same browser and let users switch between them from the User interface header.

## How it works

Every login creates its own session. authentik groups sessions created by the same browser, so a user can only switch to accounts that are already signed in from that browser.

Only the most recent login is active at a time. When a user selects another account from the switcher, authentik verifies that the browser has a live session for that account, then starts the configured account switch flow. The user must complete the authentication stages required by that flow, such as password or MFA validation.

The previous account's session stays signed in as a switch target, but its session cookie can no longer be used to act as that account. This prevents an old recorded session cookie from being replayed after the browser has switched to another account.

Logins performed through an account switch are recorded in the event log.

## Configuration

Account switches authenticate through the brand's **Account switch flow**.

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **System** > **Brands** and edit the brand you want to configure.
3. Under **Default flows**, set **Account switch flow** to the authentication flow users should complete when switching accounts.
4. Click **Update**.

Any authentication flow can be used. If no account switch flow is set, authentik uses the brand's default authentication flow.

The default authentication flow does not ask users to identify the account again during an account switch, because the selected account is already known. Password and authenticator validation still run. This is controlled by the expression policy bound to the identification stage:

```python
return not request.context.get("is_account_switch", False)
```

Custom account switch flows can use the same pattern. Bind an expression policy to the identification, password, or authenticator validation stage bindings, depending on what users should confirm when they switch back to a signed-in account. Without those policies, the flow runs in full, with the selected account already filled in.
