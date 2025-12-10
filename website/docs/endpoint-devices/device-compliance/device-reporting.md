---
title: Device reporting
sidebar_label: Device reporting
tags:
    [
        device compliance,
        compliance,
        device facts,
        device reporting,
        device check-in,
        check-in,
        facts,
    ]
---

Endpoint Devices registered with authentik via a connector, such as the [authentik Agent](./connectors.md#authentik-agent) or [Fleet](./connectors.md#fleet), regularly [check-in](#device-check-in) with authentik and report their [device facts](#device-facts).

These facts are shown on the [Devices Overview](../devices-overview.mdx) page and are also accessible to policies and can be used to make policy decisions. See [Device Compliance Policy](./device-compliance-policy.md) for more details.

## Device check-in

When a device registered with authentik reports its [device facts](#device-facts), this is called a **Device check-in**. These check-ins occur (TODO)

## Device facts

Device facts are informational snippets about a device, such as its operating system, serial number, installed applications, running processes, and more. These facts can then be used to make policy decisions. For example, you can create a policy that only allows Endpoint Devices that are running a recent OS version to access an application.

## Devices in event logs

(TODO)
