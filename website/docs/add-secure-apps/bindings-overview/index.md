---
title: authentik bindings
---

A binding is a connection between two components. In practice, a binding adds behavior to an existing authentik object by telling authentik where to evaluate a policy, user, or group, or where to insert a stage into a flow.

A policy answers the question "should this pass?" A binding decides where authentik asks that question.

:::info
For information about creating and managing bindings, refer to [Work with bindings](./work-with-bindings.md).
:::

Bindings are used throughout authentik. Many access and execution decisions are configured through bindings. The two binding types that you will work with most often are:

- **Policy bindings**, which attach a policy, user, or group to an object that supports bindings.
- **Flow-stage bindings**, which attach a stage to a flow in a specific order.

## Types of bindings

The two most common types of bindings in authentik are policy bindings and flow-stage bindings. They solve different problems:

- Use a policy binding when you want to control whether a target is allowed, denied, or shown.
- Use a flow-stage binding when you want to place a stage into a flow and decide when it should run.

## Where bindings are used

The policy binding system is shared by several authentik objects. As of the current implementation, you can bind policies, users, and groups to these targets:

- flows
- flow-stage bindings
- applications
- application entitlements
- sources
- devices
- device access groups
- notification rules
- RAC endpoints

Stages themselves are not policy binding targets. A stage is attached to a flow through a flow-stage binding, so when you bind a policy to a stage in a flow, you are binding it to that flow-stage binding.

Because of this, the same stage can be reused in multiple flows, and each flow can apply different policies to that stage.

## Relationships

```mermaid

flowchart TD
    subgraph Directory
        user[User]
        group[Group]
    end

    subgraph Policy
        policy[Policy]
        policy_binding[Policy Binding]
    end

    subgraph Application
        application[Application]
        application_entitlement[Application Entitlement]
    end
    subgraph Sources
        source[Source]
    end
    subgraph Endpoint devices
        device[Device]
        device_access_group[Device Access Group]
    end
    subgraph Events
        notification_rule[Notification Rule]
    end
    subgraph RAC Provider
        endpoint[Endpoint]
    end
    subgraph Flows
        flow[Flow]
        flow_stage_binding[Flow Stage Binding]
        stage[Stage]
    end

    policy --> policy_binding
    user --> policy_binding
    group --> policy_binding

    policy_binding --> application
    policy_binding --> application_entitlement
    policy_binding --> source
    policy_binding --> device
    policy_binding --> device_access_group
    policy_binding --> notification_rule
    policy_binding --> flow
    policy_binding --> endpoint

    flow_stage_binding --> stage
    flow --> flow_stage_binding

    policy_binding --> flow_stage_binding
```

## Policy bindings

A policy binding attaches one of the following to a target:

- a policy object
- a user
- a group

User and group bindings are simple membership checks. A user binding passes when the current user matches that user. A group binding passes when the current user is a member of that group.

This is useful when you want a direct allow or deny rule without creating a separate policy object.

Policy bindings are commonly used with applications, sources, flows, flow-stage bindings, and [application entitlements](../applications/manage_apps.mdx#application-entitlements). For example, you can bind a group directly to an application so that only members of that group can view and launch it.

Bindings are evaluated according to the target's **Policy engine mode**:

- `Any`: the target passes when any binding passes.
- `All`: the target passes only when every binding passes.

authentik evaluates enabled bindings in ascending order. The order is most noticeable when you are reading logs or combining multiple policies that return messages.

Bindings also support these options:

- **Negate**, which flips the pass or fail result of the binding.
- **Timeout**, which limits how long authentik waits for policy execution.
- **Failure result**, which controls whether a policy error is treated as pass or fail.

Policy bindings attached directly to a flow are evaluated before the flow starts. In authentication and enrollment flows, that usually means that user- and group-based checks on the flow itself cannot pass until the user has already been identified elsewhere.

If a target has no applicable bindings, authentik treats the result as passing by default.

## Flow-stage bindings

A flow-stage binding attaches a stage to a flow and defines the order in which that stage runs.

Flow-stage bindings are also called stage bindings. authentik uses them while building the flow plan that determines which stages a user will see and in what order.

This matters because stages are reusable objects. The same stage can appear in multiple flows, but each flow-stage binding can have its own policies, users, groups, order, and evaluation settings. When you bind a policy to a stage in a specific flow, you are binding it to that flow-stage binding, not to the reusable stage definition itself.

### When authentik evaluates stage-binding policies

Flow-stage bindings have two evaluation settings:

- **Evaluate when flow is planned**: authentik evaluates the binding while it is building the flow plan. If the binding does not pass at planning time, the stage is not added to the plan.
- **Evaluate when the stage is run**: authentik adds the stage to the flow plan, then evaluates the binding again immediately before the stage is shown. If the binding no longer passes, authentik removes that stage from the flow plan.

The second option is useful when the decision depends on context that is only available later in the flow. For example, after an identification stage completes, a subsequent stage binding can assess the identified user and then trigger a CAPTCHA or Deny stage as needed.

In other words:

- use **Evaluate when flow is planned** when the decision can already be made before the user reaches the stage
- use **Evaluate when the stage is run** when the decision depends on flow context that is created by an earlier stage

## What to remember

- Stages are attached to flows through flow-stage bindings.
- Policies, users, and groups can all be bound through the same policy binding system.
- The same stage can behave differently in different flows because each flow-stage binding has its own settings and bindings.
- A policy bound directly to a flow is evaluated earlier than a policy bound to a flow-stage binding.

## Common examples

### Restrict an application

By default, applications are accessible to all users. Bind a group or policy to an application when you want to limit access to specific users.

### Run a stage only for some users

Bind a policy, user, or group to the flow-stage binding when a stage should appear only for certain users in that flow. For example, only require an MFA stage for certain users.

### Scope access inside an application

Use [application entitlements](../applications/manage_apps.mdx#application-entitlements) when you need to control access to parts of an application after the user already has access to the application itself. For example, control which users have access to certain administrator functions within an application.
