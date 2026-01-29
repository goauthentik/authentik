---
title: Working with policies
---

For an overview of policies, refer to our documentation on [Policies](./index.md).

authentik provides several [standard policy types](./index.md#standard-policies), which can be configured for your specific needs. We also document several useful [expression policies](./expression.mdx#sample-expression-policies).

:::info
You can add expressions to our standard policies to further customize them.
:::

To learn more, see the [bindings](../../add-secure-apps/bindings-overview/index.md) and how to [bind policy bindings to a new application when the application is created](../../add-secure-apps/applications/manage_apps.mdx#create-an-application-and-provider-pair) documentation (for example, to configure application-specific access).

## Create a policy

To create a new policy, _either a pre-configured one or an expression policy_, follow these steps:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**, and select the type of policy. Here you select whether you want to create a custom expression policy, or a standard, out-of-the box one.
4. Define the policy and click **Finish**.

## Bind a policy to a flow, stage, application, or source

After creating the policy, you can bind it to either a:

- [flow](../../add-secure-apps/flows-stages/flow/index.md)
- [stage](../../add-secure-apps/flows-stages/stages/index.md)
- [application](../../add-secure-apps/applications/index.md)
- [source](../../users-sources/sources/index.md)

:::info
Bindings are instantiated objects themselves, and conceptually can be considered as the "connector" between the policy and the component to which it is bound. This is why you might read about "binding a binding", because technically, a binding is "spliced" into another binding, in order to intercept and enforce the criteria defined in the policy. To learn more refer to our [Bindings documentation](../../add-secure-apps/bindings-overview/index.md).
:::

### Bind a policy to a flow

These bindings control which users can access a flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. In the list of flows, click on the name of the flow to which you want to bind a policy.
4. Click on the **Policy/Group/User Bindings** tab at the top of the page.
5. Here, you can decide if you want to create a new policy and bind it to the flow (**Create and bind Policy**), or if you want to select an existing policy and bind it to the flow (**Bind existing policy/group/user**).

### Bind a policy to a stage

These bindings control which stages are applied to a flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. In the list of flows, click on the name of the flow which has the stage to which you want to bind a policy.
4. Click on the **Stage Bindings** tab at the top of the page.
5. Click the arrow (**>**) beside the name of the stage to which you want to bind a policy.
   The details for that stage displays.
6. Here, you can decide if you want to create a new policy and bind it to the stage (**Create and bind Policy**), or if you want to select an existing policy and bind it to the stage (**Bind existing policy/group/user**).

## Bind a policy to an application

These bindings control which users or groups can access an application.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**.
3. In the list of applications, click on the name of the application to which you want to bind a policy.
4. Click on the **Policy/Group/User Bindings** tab at the top of the page.
5. Here, select if you want to create a new policy and bind it to the application, or select an existing policy and bind it to the application:
    - **Create and bind Policy**
    - **Bind existing Policy/Group/User**

## Bind a policy to a source

These bindings control which users or groups can access an application.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federatin and Social login**.
3. In the list of sources, click on the name of the source to which you want to bind a policy.
4. Click on the **Policy Bindings** tab at the top of the page.
5. Here, select if you want to create a new policy and bind it to the application, or select an existing policy and bind it to the application:
    - **Create and bind Policy**
    - **Bind existing Policy/Group/User**
