---
title: Bindings
---

A binding is, simply put, a connection between two components (a flow, stage, policy, user, or group) _that adds additional content_ to one those existing components.

Take the example of a _stage binding_. A stage binding connects a stage to a flow. The "additional content" contained in the stage is now added to the flow.

Similarly, a policy binding connects a specific policy to a flow or to a stage. With the binding, the flow (or stage) will now have additional content (i.e. the policy rules).

You can also bind groups and users to another component (a policy, a stage, a flow). Or more specifically, and going one step deeper, you can also _bind a binding to a binding_. With the example above, about a group, you can create a binding for a specific group, and then bind that to a binding to a stage... with the result that everyone in that group now will see that stage (and any policies bound to that stage) as part of their flow.

Bindings are an important part of authentik; the majority of configuration options are set in bindings.

Bindings are analyzed by authetntik's Flow Plan, which starts with the flow, then assesses all of the bound policies, and then runs them in order to build out the plan.

It's important to remember that bindings are instantiated objects themselves, and conceptually can be considered as the "connector" between two components. This is why you might read about "binding a binding", because technically, a binding is "spliced" into another binding, in order to intercept and enforce the criteria defined in the second binding.

For information about creating and managing bindings, refer to [Working with bindings](./work_with_bindings.md).
