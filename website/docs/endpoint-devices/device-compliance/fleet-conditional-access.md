---
title: Fleet conditional access
sidebar_label: Fleet conditional access
tags: [device compliance, compliance, conditional access, fleet, fleetdm]
authentik_version: "2026.5"
---

authentik can be configured to restrict access to specific services so that only Fleet-registered devices are allowed.

authentik automatically retrieves the Conditional Access Root CA certificate from Fleet via the Fleet connector. The Endpoint stage then verifies the device’s Fleet-issued certificate against this Root CA. If validation succeeds, the device is bound to the user’s current authentik session.

## Prerequisites

- You must have [configured compliance](./configuration.md) in authentik
- The [Fleet connector](./connectors/fleetdm.md) must be configured in authentik
- Conditional access Root CA Certificate must be pulled from Fleet via the Fleet connector. This is an automatic process
- A Fleet Enterprise license is required

## Configuring your flow

This configuration applies to a specific flow, such as an authentication flow.

### Bind Endpoint stage to flow

The flow must have an [Endpoint stage](../../add-secure-apps/flows-stages/stages/endpoint/index.md) bound to it.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages > Flows**.
3. Select the flow that you want to modify.
4. Open the **Stage Bindings** tab and click **Create and bind stage**.
5. Select **Endpoint Stage** as the stage type, click **Next**, and configure the following settings:
    - **Name**: provide a name for the stage
    - **Connector**: select the Fleet connector
    - **Mode**: set to `Device required`
6. Click **Next**.
7. Select the order for the stage. Ensure that this places the Endpoint stage in the flow wherever you want device access to be checked.
8. Click **Finish**.
