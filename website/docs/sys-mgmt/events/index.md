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
