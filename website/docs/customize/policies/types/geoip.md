---
title: GeoIP Policy
tags:
    - policy
    - geoip
    - security
---

Use a GeoIP policy when you want to make access decisions based on where a request appears to come from.

For simple country or ASN matching, a GeoIP policy is usually easier to maintain than an [Expression policy](./expression/index.mdx).

## What it can do

A GeoIP policy can:

- allow or deny requests by country
- allow or deny requests by ASN
- compare the current login location to recent login events
- detect impossible travel patterns

:::info GeoIP Data
GeoIP support is included in authentik. For advanced setup and database management, see [GeoIP operations](../../../sys-mgmt/ops/geoip.mdx).
:::

## Country and ASN matching

Use the country and ASN fields when you want straightforward allow or deny logic based on:

- the client's country
- the client's autonomous system number

If either country or ASN matching is configured, the static part of the policy passes when any configured country or ASN match succeeds.

## Distance settings

GeoIP policies can also compare the current login against recent login history.

When distance checks are enabled, authentik evaluates the current login against the configured number of historical login events. If any comparison exceeds the allowed distance or fails the impossible-travel check, the policy fails.

- **Maximum distance**: the maximum allowed distance between a previous login location and the current login location.
- **Distance tolerance**: an additional tolerance, in kilometers, added to the maximum distance before the policy fails.
- **Historical Login Count**: how many recent login events authentik should compare against.
- **Check impossible travel**: enables an additional check based on travel speed between recent login events.
- **Impossible travel tolerance**: an additional tolerance, in kilometers, added to the built-in impossible-travel allowance.

## Create a GeoIP policy

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **New Policy** and select **GeoIP Policy**.
4. Configure the country, ASN, and optional distance settings you need.
5. Click **Create Policy**.

## Common use

GeoIP policies are often bound to:

- applications, to restrict access by network geography
- stage bindings, to trigger additional checks only for risky requests
- flows, when access to the whole flow should depend on request origin
