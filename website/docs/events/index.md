---
title: Events
---

Events are authentik's built-in logging system. Whenever any of the following actions occur, an event is created:

-   A user logs in/logs out (including the source, if available)
-   A user fails to login
-   A user sets their password

-   A user views a token

-   An invitation is used

-   A user object is written to during a flow

-   A user authorizes an application
-   A user links a source to their account

-   A user starts/ends impersonation, including the user that was impersonated

-   A policy is executed (when a policy has "Execution Logging" enabled)
-   A policy or property mapping causes an exception

-   A configuration error occurs, for example during the authorization of an application

-   Any objects is created/updated/deleted

-   An update is available

Certain information is stripped from events, to ensure no passwords or other credentials are saved in the log.

If you want to forward these events to another application, simply forward the log output of all authentik containers. Every event creation is logged there.
