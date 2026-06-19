---
title: Endpoint stage
---

The Endpoint stage checks whether the current browser or device is known to authentik's Endpoint Devices system and injects device facts into flow context.

## Overview

This stage integrates with [Endpoint Devices](../../../../endpoint-devices/index.mdx). It can associate the current session with a managed endpoint and make device facts available to policies and later stages.

## Configuration options

- **Connector**: which endpoint connector should be used to gather device information.
- **Mode**: whether endpoint verification is optional or required.

## Flow integration

Use this stage in authentication or authorization flows where device posture should influence access decisions.

The device facts gathered by this stage can then be consumed by policies or by later flow logic.

## Notes

- In **required** mode, the flow fails if the device cannot be verified.
- In **optional** mode, authentik attempts verification and can continue without attaching a device if verification does not complete in time.
