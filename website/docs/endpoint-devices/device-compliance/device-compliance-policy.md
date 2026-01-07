---
title: Device compliance policy
sidebar_label: Device compliance policy
tags: [device compliance, compliance, device access, policy]
toc_max_heading_level: 4
---

Device compliance policies are used to limit access to authentik and applications based on [Device Compliance](./index.mdx) information.

Device compliance policies are currently in development and inaccessible.

However, similar functionality can be achieved with existing stages and policies.

## Prerequisites

You must have [configured compliance](./configuration.md) in authentik and on the endpoint device.

## Accessing device facts within a flow

To access device facts within a flow, the flow must include an [Endpoint stage](../../add-secure-apps/flows-stages/stages/endpoint/index.md). The Endpoint stage fetches device facts via a configured [Connector](./connectors.md) and adds them to the [Flow context](../../add-secure-apps/flows-stages/flow/context/index.mdx).

The following example shows how to use these facts within an expression policy.

```python
flow_plan = request.context.get("flow_plan") # set a flow_plan object
device = flow_plan.context.get("device") # set a device object
name = device.name # the name of the device
facts = device.cached_facts.data
ak_logger.debug("device facts", facts=facts)
```

## Examples

The following are examples of how device compliance can currently be implemented:

### Only allow authentication via endpoint devices

If your goal is to only allow authentication via endpoint devices, this is achievable by adding an [Endpoint stage](../../add-secure-apps/flows-stages/stages/endpoint/index.md) to your authentication flow.

#### Create an Endpoint stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages > Flows**.
3. Select the authentication flow that you want to modify.
4. Open the **Stage Bindings** tab and click **Create and bind stage**.
5. Select Endpoint stage as the stage type, click **Next**, and configure the following settings:
    - **Name**: provide a name for the stage
    - **Connector**: select a connector for the stage to fetch device facts from (e.g. `authentik agent`)
    - **Mode**: set to `Device required`
6. Click **Next**.
7. Select the order for the stage. Ensure that this places the Endpoint stage in the flow wherever you want device access to be checked.
8. Click **Finish**.

### Only allow authentication via a specific type of endpoint device

If your goal is to only allow authentication via a specific type of endpoint device, this is achievable by adding an [Endpoint stage](../../add-secure-apps/flows-stages/stages/endpoint/index.md) and a [Deny stage](../../add-secure-apps/flows-stages/stages/deny.md) to your authentication flow.

The following example will only allow authentication via Apple devices.

#### Create an Endpoint stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages > Flows**.
3. Select the authentication flow that you want to modify.
4. Open the **Stage Bindings** tab and click **Create and bind stage**.
5. Select Endpoint stage as the stage type, click **Next**, and configure the following settings:
    - **Name**: provide a name for the stage
    - **Connector**: select a connector for the stage to fetch device facts from (e.g. `authentik agent`)
    - **Mode**: set to `Device required`
6. Click **Next**.
7. Select the **Order** for the stage. Ensure that this places the Endpoint stage in the flow wherever you want device access to be checked.
8. Click **Finish**.

#### Create a Deny stage

9. On the **Stage Bindings** tab, click **Create and bind stage**.
10. Select **Deny Stage** as the stage type and configure the following settings:
    - **Name**: provide a name for the stage
    - **Deny message**: provide a message explaining why access was denied
11. Click **Next**.
12. Select the **Order** for the stage. Ensure that this number is higher than the Endpoint stage created in the previous section.
13. Click **Finish**.
14. Expand the Deny stage that you just created and click **Create and bind Policy**.
15. Select **Expression policy** as the policy type, click **Next**, and configure the following settings:
    - **Name**: provide a descriptive name for the policy
    - **Expression**:
        ```python
        flow_plan = request.context.get("flow_plan")
        device = flow_plan.context.get("device")
        if device.manufacturer.lower() != "apple":
            return True
        return False
        ```
        :::info Deny stage
        Because this is a deny stage, the policy must evaluate true when a requirement is not met.
        :::

16. Click **Next** and then click **Finish**.
