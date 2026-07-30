---
title: Work with bindings
---

Bindings are configured from the object that uses them. The exact page depends on what you want the binding to control.

For the concepts behind each binding type, see [Bindings in authentik](./index.md).

## Choose the right task

| Task                                 | Start here                                                                                                                                                              | Use when                                                            |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Add a stage to a flow                | [Bind a stage to a flow](../flows-stages/stages/index.md#bind-a-stage-to-a-flow)                                                                                        | You want a flow to include a stage.                                 |
| Control whether a stage runs         | [Bind users and groups to a flow's stage binding](../flows-stages/stages/index.md#bind-users-and-groups-to-a-flows-stage-binding)                                       | You want a stage to run only for specific users or groups.          |
| Attach a policy to a target          | [Bind a policy to a flow, stage binding, application, or source](../../customize/policies/working_with_policies.md#bind-a-policy-to-a-flow-stage-application-or-source) | You want a policy to decide whether a target passes.                |
| Control application access           | [Use bindings to control access](../applications/manage_apps.mdx#use-bindings-to-control-access)                                                                        | You want to limit who can view and launch an application.           |
| Control access inside an application | [Create an application entitlement](../applications/manage_apps.mdx#create-an-application-entitlement)                                                                  | You want to grant access to a feature, role, or area inside an app. |

## General workflow

Most policy, group, and user bindings follow this pattern:

1. Log in to authentik as an administrator and open the Admin interface.
2. Open the object that should use the binding, such as an application, source, flow, or flow-stage binding.
3. Open the **Policy / Group / User Bindings** tab or expand the binding details for the object.
4. Click **Create or bind...**.
5. Create a new policy or bind an existing policy, group, or user.
6. Configure the binding options, and then click **Create**.

Flow-stage bindings use the **Stage Bindings** tab on a flow. From that tab, you can bind an existing stage or create a new stage and bind it to the flow.

## Important behavior

- If an application has no bindings, all users can access it.
- If another policy binding target has no applicable bindings, authentik treats the result as passing.
- User and group bindings require authentik to know the current user. In authentication and enrollment flows, bind user- or group-based checks to a flow-stage binding after the user is identified.
- If a stage decision depends on data collected during the flow, enable **Evaluate when stage is run** on the flow-stage binding. For more information, see [Planning and stage policies](../flows-stages/flow/planner.md#planning-and-stage-policies).
