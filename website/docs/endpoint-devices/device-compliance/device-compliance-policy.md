---
title: Device compliance policy
sidebar_label: Device compliance policy
tags: [device compliance, compliance, device access, policy]
toc_max_heading_level: 4
---

Device compliance policies are used to limit access to authentik and applications based on [Device Compliance](./index.mdx) information.

Device compliance policies are currently in development and inaccessible.

However, similar functionality can be achieved with existing stages. The following are examples of what can be achieved.

## Prerequisites

You must have [configured compliance](./configuration.md) in authentik and on the endpoint device.

## Examples

### Limit authentication to only registered endpoint devices

If your goal is to only allow registered endpoint devices, this is achievable by adding an [Endpoint stage](../../add-secure-apps/flows-stages/stages/endpoint/index.md) and a [Deny stage](../../add-secure-apps/flows-stages/stages/deny.md) to your authentication flow.

#### Create an Endpoint stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages > Flows**.
3. Select the authentication flow that you want to modify.
4. Open the **Stage Bindings** tab and click **Create and bind stage**.
5. Create a Endpoint stage (TODO)

#### Create a deny stage

6. On the **Stage Bindings** tab, click **Create and bind stage**.
7. Select **Deny Stage** as the stage type and configure the following settings:
    - **Name**: provide a name for the stage
    - **Deny message**: provide a message explaining why access was denied
8. Click **Next**.
9. Select the **Order** for the stage. Ensure that this number is higher than the Endpoint stage created in the previous section.
10. Click **Finish**.
