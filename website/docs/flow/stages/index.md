---
title: Stages
---

Stages are one of the fundamental building blocks in authentik, along with [flows](../index.md) and [policies](docs/policies/index.md).

A stage represents a single verification or logic step within a flow. You can bind one or more stages to a flow to create a customized, flexible login and authentication process.

In the following diagram of the `default-authentication-flow`, you see multiple stages, or steps, in the authentication process for a user. Policies are bound to some stages; this provides for dynamic application of a specific stage _if_ the policy criteria is met.

```mermaid
graph TD
flow_pre[["Pre-flow policies"]]
flow_pre --Binding 10--> flow_policy_0{{"Policy (Event Matcher Policy)
default-match-update"}}
flow_policy_0 --Policy denied--> done[["End of the flow"]]
flow_policy_0 --> flow_start[["Flow
Welcome to authentik!"]]
stage_0_policy_0 --Policy passed--> stage_0(["Stage (Identification Stage)
default-authentication-identification"])
stage_1_policy_0 --Policy passed--> stage_1(["Stage (Password Stage)
default-authentication-password"])
--> stage_2(["Stage (Authenticator Validation Stage)
default-authentication-mfa-validation"])
--> stage_3(["Stage (User Login Stage)
default-authentication-login"])
flow_start --> stage_0_policy_0{{"Policy (Event Matcher Policy)
default-match-configuration-error"}}
stage_0 --> stage_1_policy_0{{"Policy (Expression Policy)
default-authentication-flow-password-stage"}}
stage_0_policy_0 --Policy denied--> stage_1(["Stage (Password Stage)
default-authentication-password"])
stage_1_policy_0 --Policy denied--> stage_2(["Stage (Authenticator Validation Stage)
default-authentication-mfa-validation"])
stage_3 --> done[["End of the flow"]]
```

## Create a Stage

To create a stage, follow these steps:

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages -> Stages**.
3. Click **Create**, define the flow using the configuration settings, and then click **Finish**.

After creating the stage, you can then [bind the stage to a flow](#bind-a-stage-to-a-flow) or [bind a policy to the stage](../../policies/working_with_policies/working_with_policies.md) (the policy determines whether or not the stage will be implemented in the flow).

## Bind a stage to a flow

To bind a stage to a flow, follow these steps:

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages -> Flows**.
3. In the list of flows, click the name of the flow to which you want to bind one or more stages.
4. On the Flow page, click the **Stage Bindings** tab at the top.
5. Here, you can decide if you want to create a new stage and bind it to the flow (**Create and bind Stage**), or if you want to select an existing stage and bind it to the flow (**Bind existing stage**).
