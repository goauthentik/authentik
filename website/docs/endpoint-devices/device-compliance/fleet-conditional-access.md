---
title: Fleet conditional access for Apple devices
sidebar_label: Fleet conditional access
tags: [device compliance, compliance, conditional access, fleet, fleetdm]
authentik_version: "2026.5"
---

authentik can be configured to restrict access to specific services so that only Fleet-registered Apple devices are allowed.

authentik automatically retrieves the Conditional Access Root CA certificate from Fleet via the Fleet connector. The Endpoint stage then verifies the device’s Fleet-issued certificate against this Root CA. If validation succeeds, the device is bound to the user’s current authentik session.

## Prerequisites

- You must have [configured compliance](./configuration.md) in authentik
- The [Fleet connector](./connectors/fleetdm.md) must be configured in authentik
- Conditional access Root CA Certificate must be pulled from Fleet via the Fleet connector. This is an automatic process
- A Fleet Enterprise license is required

## Configure Fleet and devices

A Fleet Conditional Access configuration profile must be applied to every device that you wish to apply conditional access to. Please note that that this will only function on iOS and iPadOS devices that are enrolled via Apple Automated Device Enrollment (ADE). The same limitation does not apply to macOS devices.

1. Log in to your Fleet dashboard as an administrator.
2. Navigate to **Settings** > **Integrations** > **Conditional Access**.
3. Next to **Okta**, click **Connect**. Despite being named **Okta**, the same profile is used for all integrations.
4. Click the copy button to the right of **User scope profile**.
5. Save the text as a `.mobileconfig` file. Apply it as a Fleet configuration profile on any Apple device that you wish to apply conditional access to.
   Refer to the [Fleet Custom OS settings documentation](https://fleetdm.com/guides/custom-os-settings) for more information on applying configuration profiles.

## Configure authentik

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
