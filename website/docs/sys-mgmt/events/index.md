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

## Event map

The events overview renders login and audit event locations on an integrated map. By default, authentik uses the bundled "hexworld" basemap: land is rendered as a hexagonal grid across three zoom levels, with country, region, and locality labels overlaid. Because the map archive is included in authentik, it requires no external services or network requests, and therefore also works in air-gapped deployments.

Event locations are derived from GeoIP data and are accurate to city level at best. The hex-grid sizes reflect that limitation: approximately 1,000 km at the world view, 400 km at mid-range, and 130 km at the closest zoom level. Events appear as raised columns on a tilted globe: the more events a cell contains, the taller its column.

If a cell contains multiple event types, its column is divided into colored pie segments:

- **Logins**: green
- **Failed logins**: red
- **Logouts**: blue
- **Application authorizations**: purple
- **All other events**: grey

Select a column to filter the event list below to events from that cell. Custom basemaps configured under **System** > **Brands** display the same event columns over the configured tiles.

Label data is derived from [OpenStreetMap](https://openstreetmap.org/copyright) (© OpenStreetMap contributors, ODbL). Land shapes are from Natural Earth (public domain).

### Using a conventional basemap instead

To replace the default hexworld basemap with a conventional vector basemap, set the **Map tiles** field for the brand under **System > Brands**. This field takes either a `pmtiles://` archive URL or an XYZ endpoint like `/tiles/{z}/{x}/{y}.mvt`. Any non-empty value overrides the bundled default; leave it blank to keep the hexworld basemap.
