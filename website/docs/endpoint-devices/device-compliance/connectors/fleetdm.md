---
title: Fleet connector
sidebar_label: Fleet connector
tags: [device compliance, compliance, connectors, fleet, fleetdm]
---

[Fleet](https://fleetdm.com/) is an open-source device management platform designed to monitor, manage, and secure large fleets of devices.

The Fleet connector allows device information to be reported from your Fleet deployment and can optionally assign users to devices automatically.

## Preparation

- Take note of your Fleet Server URL by logging in to the Fleet admin panel and navigating to **Settings** > **Organization settings** > **Fleet web address**.
- Follow the [Fleet documentation for creating an API-only user](https://fleetdm.com/guides/fleetctl#using-fleetctl-with-an-api-only-user) and take note of its API key.

:::warning No user API keys
Do not use an API key from a normal user because these keys expire.
:::

## Configure the Fleet connector

Follow these instructions to configure the Fleet connector:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors** and click **Create**.
3. Select **Fleet Connector** as the connector type, click **Next**, and configure the following settings:
    - **Connector name**: provide a descriptive name for the connector.
    - **Fleet Server URL**: enter your `Fleet web address` URL.
    - **Fleet API Token**: enter the API key of an API-only user.
    - **Map users**: enable if you want users associated with the device in Fleet to be automatically [given access to the device via the authentik Agent](../../authentik-agent/device-authentication/index.mdx).
    - **Map teams to device access group**: enable if you want groups associated with the device in Fleet to be automatically mapped to a [device access group](../../authentik-agent/device-authentication/device-access-groups.mdx) and [given access to the device via the authentik Agent](../../authentik-agent/device-authentication/index.mdx).
4. Click **Finish**.

:::note
The **Map teams to device access group** will not detect changes to a device's groups membership in Fleet. If the device's groups change, you will need to manually configure a [device access group](../../authentik-agent/device-authentication/device-access-groups.mdx).
:::
