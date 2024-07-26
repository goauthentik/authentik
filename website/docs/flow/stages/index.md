---
title: Stages
---

Stages are one of the fundamental building blocks in authentik, along with [flows](../../flow/index.md) and [policies](../../policies/index.md).

A stage represents a single verification or logic step within a flow. You can bind one or more stages to a flow to create a customized, flexible login and authentication process.

In the following diagram of the `default-authentication-flow`, you see multiple stages, or steps, in the authentication process for a user. Policies are bound to some stages; this provides for dynamic application of a specific stage *if* the policy criteria is met.

![](./flow_diagram3.png)

## Create a Stage

To create a stage, follow these steps:

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages -> Stages**.
3. Click **Create**, define the flow using the configuration settings, and then click **Finish**.

After creating the stage, you can then:
    -   bind the stage to a flow
    -   [bind a policy to the stage](../../policies/working_with_policies/work_with_policies.md) (the policy determines whther or not the stage will be implemented in the flow)

## Bind a stage to a flow

To bind a stage to a flow, follow these steps:

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages -> Flows**.
3. Click


