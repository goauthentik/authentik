---
title: Working with policies
---

For an overview of policies, refer to our documentation on [Policies](./index.md).

authentik provides several [standard policy types](./index.md#standard-policies), which can be configured for your specific needs.

We also document how to use a policy to [whitelist email domains](./expression/whitelist_email.md) and to [ensure unique email addresses](./expression/unique_email.md).

To learn more see also [bindings](../../add-secure-apps/flows-stages/bindings/index.md) and how to [bind policy bindings to a new application when the application is created](../../add-secure-apps/applications/manage_apps.mdx#instructions) (for example, to configure application-specific access).

## Create a policy

To create a new policy, follow these steps:

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Customization -> Policies**.
3. Click **Create**, and select the type of policy.
4. Define the policy and click **Finish**.

## Bind a policy to a flow or stage

After creating the policy, you can bind it to either a [flow](../../add-secure-apps/flows-stages/flow/index.md) or to a [stage](../../add-secure-apps/flows-stages/stages/index.md).

:::info
Bindings are instantiated objects themselves, and conceptually can be considered as the "connector" between the policy and the stage or flow. This is why you might read about "binding a binding", because technically, a binding is "spliced" into another binding, in order to intercept and enforce the criteria defined in the policy. To learn more refer to our [Bindings documentation](../../add-secure-apps/flows-stages/bindings/index.md).
:::

### Bind a policy to a flow

These bindings control which users can access a flow.

1. Log in as an admin to authentik, and open the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages -> Flows**.
3. In the list of flows, click on the name of the flow to which you want to bind a policy.
4. Click on the **Policy/Group/User Bindings** tab at the top of the page.
5. Here, you can decide if you want to create a new policy and bind it to the flow (**Create and bind Policy**), or if you want to select an existing policy and bind it to the flow (**Bind existing policy/group/user**).

### Bind a policy to a stage

These bindings control which stages are applied to a flow.

1. Log in as an admin to authentik, and open the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages -> Flows**.
3. In the list of flows, click on the name of the flow to which you want to bind a policy.
4. Click on the **Stage Bindings** tab at the top of the page.
5. Click the arrow (**>**) beside the name of the stage to which you want to bind a policy.
   The details for that stage displays.
6. Here, you can decide if you want to create a new policy and bind it to the stage (**Create and bind Policy**), or if you want to select an existing policy and bind it to the stage (**Bind existing policy/group/user**).
