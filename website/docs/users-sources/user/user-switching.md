---
title: User switching
---

authentik can keep multiple users signed in within the same browser and let users switch between them from the User interface header.

## How it works

Every login creates its own session. authentik groups sessions created by the same browser, so a user can only switch to users that are already signed in from that browser.

Only the most recent login is active at a time. When a user selects another user from the switcher, authentik verifies that the browser has a live session for that user, then starts the configured user switch flow. The user must complete the authentication stages required by that flow, such as password or MFA validation.

The previous user's session stays signed in as a switch target, but its session cookie can no longer be used to act as that user. This prevents an old recorded session cookie from being replayed after the browser has switched to another user.

Logins performed through a user switch are recorded in the event log.

## Configuration

User switches authenticate through the brand's **User switch flow**. If no user switch
flow is set, the switcher is disabled and the switch endpoint cannot be used.

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **System** > **Brands** and edit the brand you want to configure.
3. Under **Default flows**, set **User switch flow** to the authentication flow users should complete when switching users.
4. Click **Update**.

Any authentication flow can be used. To reuse the default authentication flow for switching, set it
explicitly as the **User switch flow**.

During a user switch, the selected user is already known and is available to the flow as
`pending_user`. To skip a stage only during user switches, bind an expression policy to that
stage binding:

```python
flow_plan = request.context.get("flow_plan")
is_user_switch = bool(flow_plan and flow_plan.context.get("user_switch_from_user"))

return not is_user_switch
```

Bind the policy to the identification, password, authenticator validation, or other stage binding
depending on what users should confirm when they switch back to a signed-in user. Without these
policies, the selected user switch flow runs in full.

## Require only MFA for recently used users

To require only MFA when the selected user was used in the last 24 hours, create a dedicated
user switch flow with a Password stage, an Authenticator Validation stage, and a User Login stage.
Then bind the following expression policy to the Password stage binding:

```python
from datetime import timedelta

from django.utils import timezone

from authentik.core.models import AuthenticatedSession

flow_plan = request.context.get("flow_plan")
user = None
is_user_switch = False
if flow_plan:
    user = flow_plan.context.get("pending_user")
    is_user_switch = bool(flow_plan.context.get("user_switch_from_user"))

now = timezone.now()
if not is_user_switch or not user:
    return True

recently_used = AuthenticatedSession.objects.filter(
    user=user,
    session__expires__gt=now,
    session__last_used__gte=now - timedelta(hours=24),
).exists()

return not recently_used
```

When the policy returns `False`, authentik skips the Password stage and continues to the
Authenticator Validation stage. When no live session for that user has been used in the last
24 hours, the Password stage runs and the user completes the full password plus MFA flow.
