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

The events overview renders login and audit event locations on a built-in map. By default authentik uses a bundled "hexworld" basemap: land drawn as a hexagonal grid at three zoom bands, with country, region, and locality labels layered on top. The archive ships as part of the web bundle, so the map draws with no tile server, no external service, and no online request, and it works in air-gapped deployments.

Event locations come from GeoIP and are city-accurate at best. The hex bands are sized to match: about 1000 km at world view, 400 km mid-range, and 130 km at closest zoom. Cells brighten as event counts increase.

Label data is derived from [OpenStreetMap](https://openstreetmap.org/copyright) (© OpenStreetMap contributors, ODbL). Land shapes are from Natural Earth (public domain).

### Using a conventional basemap instead

To replace the hexworld default with a conventional vector basemap, set a tile URL template on the brand under **System > Brands** — the **Map tiles** field takes either a `pmtiles://` archive URL or an XYZ endpoint like `/tiles/{z}/{x}/{y}.mvt`. Any non-empty value overrides the bundled default; leave it blank to keep hexworld.
