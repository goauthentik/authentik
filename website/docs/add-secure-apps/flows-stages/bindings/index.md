---
title: Bindings
---

A binding is, simply put, a connection between two components (a flow, stage, policy, user, or group). The use of a binding adds additional functionality to one those existing components; for example, a policy binding can cause a new stage to be presented within a flow to a specific user or group.

:::info
For information about creating and managing bindings, refer to [Working with bindings](./work_with_bindings.md).
:::

Bindings are an important part of authentik; the majority of configuration options are set in bindings.

Bindings are analyzed by authentik's Flow Plan, which starts with the flow, then assesses all of the bound policies, and then runs them in order to build out the plan.

The two most common types of bindings in authentik are:

- stage bindings
- policy bindings
- user and group bindings

A _stage binding_ connects a stage to a flow. The "additional content" (i.e. the content in the stage) is now added to the flow.

A _policy binding_ connects a specific policy to a flow or to a stage. With the binding, the flow (or stage) will now have additional content (i.e. the policy rules).

You can also bind groups and users to another component (a policy, a stage, a flow, etc.). For example, you can create a binding for a specific group, and then [bind that to a stage binding](../stages/index.md#bind-users-and-groups-to-a-flows-stage-binding), with the result that everyone in that group now will see that stage (and any policies bound to that stage) as part of their flow. Or more specifically, and going one step deeper, you can also _bind a binding to a binding_.

Bindings are also used for [Application Entitlements](../../applications/manage_apps.mdx#application-entitlements), where you can bind specific users or groups to an application as a way to manage who has access to the application.

It's important to remember that bindings are instantiated objects themselves, and conceptually can be considered as a "connector" between two components. This is why you might read about "binding a binding", because technically, a binding is "spliced" into another binding, in order to intercept and enforce the criteria defined in the second binding.

:::info
Be aware that some stages and flows do not allow user or group bindings, because in certain scenarios (authentication or enrollment), the flow plan doesn't yet know who the user or group is.
:::
