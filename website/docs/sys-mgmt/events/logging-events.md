---
title: Logging events
---

Logs are a vital tool for system diagnostics, event auditing, user management, reporting, and more. They capture detailed information about each event including the client's IP address, the user involved, the date and time, and the specific action taken.

Event logging in authentik is highly configurable. You can set the [retention period](./index.md#event-retention-and-forwarding) for storing and displaying events, specify which events should trigger a [notification](./notifications.md), and access low-level details about when and where each event occurred.

## Troubleshooting with event logs

For guidance on troubleshooting with logs, including setting log levels (info, warning, etc.), enabling `trace` mode, viewing historical logs, and streaming logs in real-time, see [Capturing logs in authentik](../../troubleshooting/logs.mdx).

## Enhanced audit logging :ak-enterprise

In the enterprise version, two enhancements make reading the logs even easier:

- the Event details page in the user interface presents abstracted and easily accessible information about each event in an easy-to-access table.

- for any event that involves the creation or modification of an object, the corresponding code differences are displayed, allowing for comparison of the previous and new configuration settings or values. For example, if an authentik administrator updates a user's email address, both the old and new email addresses are displayed in the event's detailed view. (In the open source version, event details only show that a change was made and which application and model was involved.)

![](./events-diffs.png)

You can view audit details in the following areas of the authentik Admin interface:

- **Admin interface > Dashboards > Overview**: In the **Recent events** section click an event name to view its details.

- **Admin interface > Events > Logs**: In the event list, click the arrow toggle next to the event you want to view.

## Viewing events in maps and charts :ak-enterprise

With the enterprise version, you can view recent events on both a world map view with pinpoints indicating where each event occurred and also a color-coded chart that highlights event types and volume.

![](./event-map-chart.png)

## Advanced queries for event logs:ak-enterprise {#tell-me-more}

You can construct advanced queries, based on [DjangoQL](https://github.com/ivelum/djangoql), to find specific event logs. In the Admin interface, navigate to **Events > Logs**, and then use the auto-complete in the **Search** field or enter your own queries to return results with greater specificity.

- **Model/object**: `action`, `event_uuid`, `app`, `client_ip`, `user`, `brnad`, `context`, `created`

- **Operators**: `=`, `!=`, `~`, `!~`

- **Values**: `True`, `False`, `None`

- **Example queries**: `action = "login"`, `app startswith "N"`
