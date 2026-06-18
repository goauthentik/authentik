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

Account switches authenticate through the brand's **Account switch flow**. If no account switch
flow is set, the switcher is disabled and the switch endpoint cannot be used.

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **System** > **Brands** and edit the brand you want to configure.
3. Under **Default flows**, set **Account switch flow** to the authentication flow users should complete when switching accounts.
4. Click **Update**.

Any authentication flow can be used. To reuse the default authentication flow for switching, set it
explicitly as the **Account switch flow**.

During an account switch, the selected account is already known and is available to the flow as
`pending_user`. To skip a stage only during account switches, bind an expression policy to that
stage binding:

```python
return not request.context.get("is_account_switch", False)
```

Bind the policy to the identification, password, authenticator validation, or other stage binding
depending on what users should confirm when they switch back to a signed-in account. Without these
policies, the selected account switch flow runs in full.

## Require only MFA for recently used accounts

To require only MFA when the selected account was used in the last 24 hours, create a dedicated
account switch flow with a Password stage, an Authenticator Validation stage, and a User Login stage.
Then bind the following expression policy to the Password stage binding:

```python
from datetime import timedelta

from django.utils import timezone

from authentik.core.models import AuthenticatedSession

flow_plan = request.context.get("flow_plan")
user = None
if flow_plan:
    user = flow_plan.context.get("pending_user")

now = timezone.now()
if not request.context.get("is_account_switch", False) or not user:
    return True

recently_used = AuthenticatedSession.objects.filter(
    user=user,
    session__expires__gt=now,
    session__last_used__gte=now - timedelta(hours=24),
).exists()

return not recently_used
```

When the policy returns `False`, authentik skips the Password stage and continues to the
Authenticator Validation stage. When no live session for that account has been used in the last
24 hours, the Password stage runs and the user completes the full password plus MFA flow.
