---
title: Endpoint stage
---

This stage integrates with [Endpoint Device](../../../../endpoint-devices/index.mdx) functionality, allowing you to verify whether a device executing a flow is regsistred with authentik.

The Endpoint stage fetches [device facts](../../../../endpoint-devices/device-compliance/device-reporting.md#device-facts) via a configured [connector](../../../../endpoint-devices/device-compliance/connectors.md) for use in the flow. These device facts can be used by other stages and policies to make device compliance decisions.

### Connector

Select the [connector](../../../../endpoint-devices/device-compliance/connectors.md) that the Endpoint stage should use to obtain device information.

### Mode

Select whether an endpoint device is required for the stage to succeed or not.
