---
title: RAC Connection Settings
---

## About RAC connection settings

The RAC provider utilises [Apache Guacamole](https://guacamole.apache.org/) for establishing SSH, RDP and VNC connections. RAC supports the use of Apache Guacamole connection configurations.

For a full list of possible configurations, see the [Apache Guacamole connection configuration documentation](https://guacamole.apache.org/doc/gug/configuring-guacamole.html#configuring-connections).

## How to apply an RAC connection setting

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the **Edit** icon on the RAC provider that requires an Apache Guacamole connection configuration.
4. In the **Settings** codebox enter the name and value of the desired Apache Guacamole connection configuration.
5. Click **Update**.

## Example

Utilizing RAC connection settings to enable [SSH public key authentication](./rac-public-key.md).
