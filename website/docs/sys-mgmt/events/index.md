---
title: Events
---

Events are authentik's built-in logging system. Every event is logged, whether it is initiated by a user or by authentik.

Certain information is stripped from events to ensure that no passwords or other credentials are saved in the log.

## About notifications

Events can be used to define [notification rules](notifications.md), with specified [transport options](transports.md) of either local (shown in the authentik UI), email, or webhook.

## About logging

Event logging in authentik provides several layers of transparency about user and system actions, from a quick view on the Overview dashboard, to a full, searchable list of all events, with a volume graph to highlight any spikes, in the Admin interface under **Events > Logs**.

Refer to our [Logging documentation](./logging-events.mdx) for more information.

## Event retention and forwarding

The event retention setting is configured in the **System > Settings** area of the Admin interface, with the default being set to 365 days.

If you want to forward these events to another application, forward the log output of all authentik containers. Every event creation is logged with the log level "info". For this configuration, it is also recommended to set the internal retention time period to a short time frame (for example, `days=1`).

If you want to forward authentik events to another system, see [Log forwarding](./log-forwarding.mdx).

## Event map :ak-enterprise {#event-map}

The event map groups events into areas based on [GeoIP data](../ops/geoip.mdx). Each area appears as a column. Taller columns contain more events, and segments within a column represent different event types. Select a column to filter the event list to events in that area.

GeoIP locations are accurate to city level at best. By default, authentik uses a bundled hexagonal basemap with country, region, and locality labels. The bundled basemap does not require an external tile service, so it works in [air-gapped environments](../../install-config/air-gapped.mdx).

### Configure a custom basemap

To replace the bundled basemap, navigate to **System** > **Brands**, edit the applicable brand, and configure **Map tiles**. The field accepts either a PMTiles archive URL that uses the `pmtiles://` protocol or an XYZ vector tile URL template with `{z}`, `{x}`, and `{y}` placeholders. Leave the field empty to use the bundled basemap.

Users' browsers must be able to access the configured tile source.
