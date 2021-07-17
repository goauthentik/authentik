---
title: Radius Outpost
---

:::info
This feature is still in technical preview, so please report any Bugs you run into on [GitHub](https://github.com/goauthentik/authentik/issues)
:::

You can configure a Radius Provider for applications that don't support any other protocols or require Radius.

Currently, only authentication requests are supported.

Authentication requests against the Radius Server use a flow in the background. This allows you to use the same policies and flows as you do for web-based logins. The only limitation is that currently only identification and password stages are supported, due to how Radius works.
