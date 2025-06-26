---
title: Logging events
---

Logs are an important tool for system diagnoses, event auditing, user management, reports, and so much more. Detailed information about events are captured, including the IP address of the client that triggered the event, the user, the date and timestamp, and the exact action made.

Event logging in authentik is highly configurable; you can define the [retention period](./index.md#event-retention-and-forwarding) for storing and displaying events, configure which exact events should trigger a [notification](./notifications.md), and view low-level details about when and where the event happened.

## Enhanced audit logging (Enterprise)

In the enterprise version, each Event details page in the UI, details about each event are abstracted and displayed in an easy-to-access table, and for any event that involves an object being created or modified, the code `diffs` are displayed as well. This allows you to quickly see the previous and new configuration settings.

For example, say an authentik administraotr updates a user's email address; the old email address and the new one are shown when you drill down in that event's details.

![](./events-diffs.png)

Areas of the authentik UI where you can view these audits details are:

- **Admin interface > Dashboards > Overview**: In the **Recent events** section, click the name of an event to view details.

- **Admin interface > Events > Logs**: In the list of events, click the arrow toggle beside the name of the even that you want to view details for.

## Viewing events in maps and charts (Enterprise)

With the enterprise version, you can view recent events on both a world map view with pinpoints of where events occurred and also as a color-coded chart displaying type of event and volume of each type.

![](./event-map-chart.png)

### Troubleshooting with event logs

For details about troubleshooting using logs, including setting the log level (info, warning, etc.), enabling `trace` mode, viewing past logs, and streaming logs in real-time, refer to [Capturing logs in authentik](../../troubleshooting/logs.mdx).
