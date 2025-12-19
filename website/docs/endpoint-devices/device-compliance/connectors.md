---
title: Connectors
sidebar_label: Connectors
tags: [device compliance, compliance, connectors, authentik Agent, fleet]
---

Connectors allow device information to be reported to authentik.

They can be used standalone or alongside the [authentik Agent](../authentik-agent/index.mdx).

Currently, the only supported connectors is the [authentik Agent](#authentik-agent)

## Connectors

The following connectors are currently supported:

### authentik Agent

- Unlike other connectors, the agent connector is used by the agent directly compared to other connectors talking to separate systems and APIs to integrate with other agents. Hence the functionality of the agent connector behaves differently than other connectors.
- the agent connector mainly holds configuration for the agent itself, as well as implementing certain platform specific protocols like Apple's Platform SSO.

## Adding a connector

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors** and click **Create**.
3. Select the connector type and click **Next**, and configure the following required settings:
    - **Connector name**: provide a descriptive name for the connector.
    - **Refresh interval**: select how often the agent will attempt to update it's configuration.
    - **Enabled**: enable or disable the connector.
4. Click **Finish**.

## Editing a connector

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**.
3. Click on the connector that you wish to edit.
4. Update any settings that you want to change.
5. Click **Update**.

## Deleting a connector

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**.
3. Select the connector that you wish to delete.
4. Click **Delete**.
