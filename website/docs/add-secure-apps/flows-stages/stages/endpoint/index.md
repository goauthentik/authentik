---
title: Endpoint stage
---

This stage integrates with [Endpoint Device](../../../../endpoint-devices/index.mdx) functionality and allows authentik to verify whether the device executing a flow is registered.

The Endpoint stage fetches [device facts](../../../../endpoint-devices/device-compliance/device-reporting.md#device-facts) via a configured [connector](../../../../endpoint-devices/device-compliance/connectors.md) and injects them into the flow context. These device facts can be used by other stages and policies to make device compliance decisions.

## Connector

Select the [connector](../../../../endpoint-devices/device-compliance/connectors.md) that the Endpoint stage will use to obtain device facts.

## Mode

Select whether the presence of a registered endpoint device is required for the stage to succeed.
