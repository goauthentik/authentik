---
title: Flow Planner
---

The Flow Planner is the part of authentik that turns a configured [flow](./index.md) into the ordered list of stages that will run for a specific request.

A flow describes the possible sequence of stages. A flow plan is the per-session execution plan created from that configuration after authentik checks the request, the user, and the policies bound to the flow and its stage bindings.

## How the planner works

When a flow starts, authentik creates or restores a flow plan before presenting the next stage. During planning, authentik:

1. Verifies that the flow can be used in the current authentication context.
2. Evaluates policies bound directly to the flow.
3. Loads the flow's stage bindings in order.
4. Evaluates stage binding policies when **Evaluate when flow is planned** is enabled.
5. Stores the resulting ordered stage list and [flow context](./context/index.mdx) in the user's session.

The [flow executor](./executors/if-flow.md) then presents the first planned stage. When the stage completes successfully, authentik removes it from the plan and continues with the next stage. When no stages remain, the flow has completed.

## Planning and stage policies

Stage binding policies can be evaluated at two different times:

- **Evaluate when flow is planned**: The policy is evaluated when the flow plan is created. If the policy does not pass, that stage is not included in the plan.
- **Evaluate when stage is run**: The policy is evaluated immediately before the stage is presented. If the policy does not pass at that point, authentik skips that stage and continues with the next planned stage.

Both options can be enabled for the same stage binding. Use planning-time evaluation when you want the plan to reflect the stage list known at the start of execution. Use run-time evaluation when a policy depends on data that might be added to the flow context by earlier stages.

For example, a password stage usually depends on the user identified by an earlier identification stage. If a policy for a later stage depends on `pending_user`, evaluate that policy when the stage is run, or ensure `pending_user` is already present when the plan is created.

## Inspecting a plan

Use the [Flow Inspector](./inspector.md) to see the current stage, the next planned stage, plan history, and current plan context while a flow is executing.

The Inspector is especially useful when a stage is missing from a flow execution. A missing stage usually means one of the stage binding policies did not pass when the plan was created, or did not pass when the stage was re-evaluated before being shown.

## Caching and session state

authentik can cache flow plans so repeated executions of the same flow for the same user do not need to rebuild the same stage list every time. The active plan for a running flow is stored in the HTTP session, so browser-based and API-based flow executors must keep using the same session while the flow is running.

If flow behavior changes after editing stage bindings or policies, start a new flow execution before troubleshooting. Existing sessions may already have a plan in progress.
