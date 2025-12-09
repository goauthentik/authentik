---
title: Device compliance policy
sidebar_label: Device compliance policy
tags: [device compliance, compliance, device access]
toc_max_heading_level: 4
---

Device compliance policies are used to limit access to authentik and applications based on [Device Compliance](./index.mdx) information.

Device compliance policies are still in development and currently inaccessible.

However, similar functionality can be achieved with existing stages. The following are examples of what can be achieved.

## Prerequisites

You must have [configured compliance](./configuration.md) in authentik and on the Endpoint device.

## Examples

### Limit authentication to only registered Endpoint Devices

If your goal is to only allow registered Endpoint Devices, this is achievable by adding an Endpoint stage (add link to endpoint stage) and a [Deny stage](../../add-secure-apps/flows-stages/stages/deny.md) to your authentication flow.

#### Create endpoint stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages > Flows**.
3. Select the authentication flow that you want to modify.
4. Open the **Stage Bindings** tab and click **Create and bind stage**

#### Create deny stage
