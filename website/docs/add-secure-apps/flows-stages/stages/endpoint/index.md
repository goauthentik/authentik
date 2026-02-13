---
title: Endpoint stage
---

This stage integrates with the [Endpoint Device](../../../../endpoint-devices/index.mdx) functionality and allows authentik to verify whether the device executing a flow is registered.

The Endpoint stage fetches [device facts](../../../../endpoint-devices/device-compliance/device-reporting.md#device-facts) via a configured [connector](../../../../endpoint-devices/device-compliance/connectors/index.mdx) and injects them into the flow context. These device facts can be used by other stages and policies to make device compliance decisions.

## Connector

Select the [connector](../../../../endpoint-devices/device-compliance/connectors/index.mdx) that the Endpoint stage will use to obtain device facts.

## Mode

Select whether the presence of a registered endpoint device is required for the stage to succeed.

- If the mode is set to required, and device verification fails, the user is not able to proceed with the flow.
- If the mode is set to optional, authentik will attempt to verify the device, and if it doesn't receive a response within the specified `challenge_idle_timeout`, authentik will continue without attaching a device to the flow.
