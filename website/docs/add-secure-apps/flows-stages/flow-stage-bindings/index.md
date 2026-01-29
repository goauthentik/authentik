---
title: Stage bindings
---

You can use a binding to determine which exact [stages](../stages/index.md) (all of the _steps_ within a flow) are presented to a user (or a group).

A _stage binding_ connects a stage to a flow. The "additional content" (i.e. the content in the stage) is now added to the flow.

:::info
Be aware that some stages and flows do not allow user or group bindings, because in certain scenarios (authentication or enrollment), the flow plan doesn't yet know who the user or group is.
:::

For an overview about all the different types of bindings in authentik and how they are used, refer to [About authentik bindings](../../bindings-overview/index.md).
