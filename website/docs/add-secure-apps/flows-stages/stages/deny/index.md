---
title: Deny stage
---

The Deny stage stops the current flow immediately.

## About the deny stage

Use this stage when the flow should end with access denied, including cases where the user is not signed in yet and group-based permissions are not available.

## Configuration options

This stage has no stage-specific configuration options.

## Flow integration

Bind this stage where a flow should stop after a policy or earlier stage determines that the user must not continue.

## Notes

:::caution
To use this stage effectively, make sure **Evaluate when flow is planned** is disabled on the stage binding. See [Planning and stage policies](../../flow/planner.md#planning-and-stage-policies).
:::

If the binding is evaluated during flow planning, the denial can happen earlier than intended and skip the checks that were meant to decide whether the user should be denied.

### Example: block a known IP range

One common use case is to bind a Deny stage to an expression policy that blocks requests from a specific IP range.

For example:

1. Create a Deny stage.
2. Create an [Expression policy](../../../../customize/policies/types/expression/index.mdx) with logic such as:

```python
from ipaddress import ip_network

return ak_client_ip in ip_network("203.0.113.0/24")
```

3. Bind that policy to the Deny stage in the flow.

When the policy passes, the Deny stage runs and the flow stops immediately.

### Example: Block password recovery for inactive users

Account deactivation prevents authentication, but it does not automatically prevent recovery stages from sending email or changing a password. To stop inactive users before those actions occur:

1. Add a Deny stage to the recovery flow after the Identification stage and before the Email stage.
2. Create an [Expression policy](../../../../customize/policies/types/expression/index.mdx) with the following expression:

    ```python
    pending_user = request.context.get("pending_user")

    return bool(
        pending_user
        and pending_user.pk
        and not pending_user.is_active
    )
    ```

3. Bind the policy to the Deny stage binding.
4. On the Deny stage binding, disable **Evaluate when flow is planned** and enable **Evaluate when stage is run**. The policy must run after the Identification stage adds `pending_user` to the flow context.

The Deny stage runs only when the identified user exists and is inactive. Active users and placeholder users that represent unknown identifiers skip the Deny stage.

:::danger Account state disclosure
The Deny stage produces a different response for an inactive account than the **Email sent.** challenge that the Email stage displays for unknown and active accounts. An attacker can use this difference to determine that an account exists or is inactive.

Use this configuration only if disclosing account state is acceptable. A Deny stage cannot both stop recovery and preserve the Email stage's indistinguishable response.
:::
