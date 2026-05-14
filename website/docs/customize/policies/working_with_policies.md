---
title: Working with policies
tags:
    - policy
    - access-control
    - how-to
---

For an overview of policies, refer to our documentation on [Policies](./index.md).

authentik provides several [built-in policy types](./types/index.mdx), which can be configured for your specific needs. We also document several useful [expression policy examples](./types/expression/index.mdx#sample-expression-policies).

:::info
You can add expressions to built-in policies to further customize them.
:::

To learn more, see the [bindings](../../add-secure-apps/bindings-overview/index.md) documentation and the guide on how to [bind a policy to a new application when the application is created](../../add-secure-apps/applications/manage_apps.mdx#create-an-application-and-provider-pair) (for example, to configure application-specific access).

## Create a policy

To create a policy:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **New Policy**.
4. Select the policy you want to create.
5. Configure the policy-specific settings.
6. Click **Create Policy**.

If you are not sure which policy type to choose, see [Types of policies in authentik](./types/index.mdx).

## Bind a policy to a flow, stage, application, or source

After creating the policy, you can bind it to either a:

- [flow](../../add-secure-apps/flows-stages/flow/index.md)
- [stage binding](../../add-secure-apps/flows-stages/stages/index.md)
- [application](../../add-secure-apps/applications/index.md)
- [source](../../users-sources/sources/index.md)

:::info
Bindings are instantiated objects themselves, and conceptually can be considered the "connector" between the policy and the component to which it is bound. This is why you might read about "binding a binding", because technically, a binding is "spliced" into another binding in order to intercept and enforce the criteria defined in the policy. To learn more, refer to our [Bindings documentation](../../add-secure-apps/bindings-overview/index.md).
:::

### Bind a policy to a flow

These bindings control which users can access a flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. In the list of flows, click on the name of the flow to which you want to bind a policy.
4. Click on the **Policy/Group/User Bindings** tab at the top of the page.
5. Either create a new policy and bind it immediately with **Create and bind Policy**, or attach an existing policy, group, or user with **Bind existing policy/group/user**.

### Bind a policy to a stage binding

These bindings control which stages are applied to a flow.

:::info
When you bind a policy to a stage binding, this task is done per flow, and does not carry across to other flows that might use this same stage.
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. In the list of flows, click on the name of the flow which has the stage to which you want to bind a policy.
4. Click on the **Stage Bindings** tab at the top of the page.
5. Click the arrow (**>**) beside the name of the stage to which you want to bind a policy. The details for that stage are displayed.
6. Either create and bind a new policy, or bind an existing policy, group, or user.

If the policy depends on request data that is only known after the user has interacted with the flow, configure the stage binding to **Evaluate when stage is run** instead of only at planning time.

### Bind a policy to an application

These bindings control which users or groups can access an application.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**.
3. In the list of applications, click on the name of the application to which you want to bind a policy.
4. Click on the **Policy/Group/User Bindings** tab at the top of the page.
5. Either create and bind a new policy, or bind an existing policy, group, or user.

### Bind a policy to a source

These bindings control which users or groups can access a source.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**.
3. In the list of sources, click on the name of the source to which you want to bind a policy.
4. Click on the **Policy Bindings** tab at the top of the page.
5. Either create and bind a new policy, or bind an existing policy, group, or user.

For background on policy ordering, engine mode, and binding options, see [Policy bindings and evaluation](./bindings.md).
