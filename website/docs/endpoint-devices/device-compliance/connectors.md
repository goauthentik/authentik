---
title: Connectors
sidebar_label: Connectors
tags: [device compliance, compliance, connectors, authentik Agent, fleet]
toc_max_heading_level: 4
---

Connectors allow device information to be reported to authentik. They can be used standalone or alongside the [authentik Agent](../authentik-agent/index.mdx).

Currently, the only supported connector is the [authentik Agent](#authentik-agent).

## Connectors

The following connectors are currently supported:

### authentik Agent

- Unlike other connectors, the agent connector is used by the agent directly compared to other connectors talking to separate systems and APIs to integrate with other agents. Hence the functionality of the agent connector behaves differently than other connectors.
- the agent connector mainly holds configuration for the agent itself, as well as implementing certain platform specific protocols like Apple's Platform SSO.

#### Challenge Key

The Agent Connector requires a **Challenge Key** (Certificate Keypair) to be configured when using the [Endpoint Stage](../../add-secure-apps/flows-stages/stages/endpoint/index.md). This keypair is used to sign challenges sent to the [browser extension](./browser-extension.mdx) for device verification.

Without a Challenge Key configured, the Endpoint Stage will silently skip device verification.

To configure a Challenge Key:

1. Navigate to **System** > **Certificates** and create a new certificate keypair, or select an existing one.
2. Navigate to **Endpoint Devices** > **Connectors** and edit your Agent Connector.
3. Set the **Challenge Key** field to your certificate keypair.
4. Click **Update**.

## Adding a connector

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors** and click **Create**.
3. Select the connector type and click **Next**, and configure the following required settings:
    - **Connector name**: provide a descriptive name for the connector.
    - **Refresh interval**: select how often the agent will attempt to update its configuration.
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
