---
title: Deny stage
---

The Deny stage stops the current flow immediately.

## Overview

Use this stage when the flow should end with access denied, including cases where the user is not signed in yet and group-based permissions are not available.

## Configuration options

This stage has no stage-specific configuration options.

## Flow integration

Bind this stage where a flow should stop after a policy or earlier stage determines that the user must not continue.

## Notes

:::caution
To use this stage effectively, make sure **Evaluate when flow is planned** is disabled on the stage binding.
:::

If the binding is evaluated during flow planning, the denial can happen earlier than intended and skip the checks that were meant to decide whether the user should be denied.

### Example: block a known IP range

One common pattern is to bind a Deny stage to an expression policy that blocks requests from a specific IP range.

For example:

1. Create a Deny stage.
2. Create an [Expression policy](../../../../customize/policies/expression.mdx) with logic such as:

```python
from ipaddress import ip_network

return ak_client_ip in ip_network("203.0.113.0/24")
```

3. Bind that policy to the Deny stage in the flow.

When the policy passes, the Deny stage runs and the flow stops immediately.
