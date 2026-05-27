---
title: Flow Planner
---

The Flow Planner is the component of authentik that takes a configured [flow](./index.md) and, for each incoming request for that flow, determines the specific stages to run and the order in which they will run.

A flow describes a sequence of stages and policies. A flow plan is the per-session execution plan derived from that flow after authentik evaluates the request, the user, and the policies bound to the flow and its stage bindings.

## How the planner works

When a flow is executed, authentik creates a flow plan and does the following:

1. Verifies that the flow can be used in the current authentication context.
2. Evaluates policies bound directly to the flow.
3. Loads the flow's stage bindings in order.
4. Evaluates stage binding policies when **Evaluate when flow is planned** is enabled.
5. Stores the resulting ordered stage list and [flow context](./context/index.mdx) in the user's session.

The [flow executor](./executors/if-flow.md) then presents the first stage of the flow plan. When the stage completes successfully, authentik removes it from the flow plan and continues with the next stage. When no stages remain, the flow plan has completed.

## Planning and stage policies

Stage binding policies can be evaluated at two different times:

- **Evaluate when flow is planned**: The policy is evaluated when the flow plan is created. If the policy does not pass, that stage is not included in the plan.
- **Evaluate when stage is run** (_default_): The policy is evaluated immediately before the stage is presented. If the policy does not pass at that point, authentik skips that stage and continues with the next planned stage.

Both options can be enabled for the same stage binding. Use planning-time evaluation when a policy can be evaluated before any stages run. Use run-time evaluation when a policy depends on data that might be added to the flow context by earlier stages.

For example, a password stage usually depends on the user identified by an earlier identification stage. If a policy for a later stage depends on `pending_user`, evaluate that policy when the stage is run, or ensure `pending_user` is already present when the plan is created.

## Inspecting a plan

Use the [Flow Inspector](./inspector.md) to execute a flow and, while it executes, view the current stage, the next planned stage, the plan history, and the current plan context.

The Flow Inspector is accessed via the Flow Overview page and is particularly useful for troubleshooting flows and determining why stage binding policies fail to pass. It's also useful to evaluate values for use in policies.

## Caching and session state

authentik can cache flow plans so repeated executions of the same flow for the same user do not need to rebuild the same stage list every time. The active plan for a running flow is stored in the HTTP session, so browser-based and API-based flow executors must keep using the same session while the flow is running.

If flow behavior changes after editing stage bindings or policies, start a new flow execution before troubleshooting. Existing sessions may already have a plan in progress.
