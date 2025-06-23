---
title: Events
---

Events are authentik's built-in logging system. Every event is logged, whether it is initiated by a user or by authentik.

Events can be used to define [notification rules](notifications.md), with specified [transport options](transports.md) of either local (in the authentik UI), email, or webhook.

Certain information is stripped from events, to ensure that no passwords or other credentials are saved in the log.

## Event retention and forwarding

The event retention is configured in the **System > Settings** area of the Admin interface, with the default being set to 365 days.

If you want to forward these events to another application, forward the log output of all authentik containers. Every event creation is logged with the log level "info". For this configuration, it is also recommended to set the internal retention time period to a short time frame (for example, `days=1`).

## Audit logging
