---
title: Policy Bindings and Evaluation
tags:
    - policy
    - bindings
    - access-control
---

For a high-level overview of the available policy types, see [Policies](./index.md). This page focuses on the mechanics: where policies are attached, how bindings work, and how authentik evaluates multiple results.

## What a binding does

A policy answers a question like "should this pass?" A binding decides where authentik asks that question.

For example:

- a policy bound to a **flow** controls whether the flow can be used
- a policy bound to a **stage binding** controls whether that stage runs inside the flow
- a policy bound to an **application** controls whether the user can access that application
- a policy bound to a **source** controls whether that source can be used

In the same binding UI, you can also bind a **user** or **group** directly. Those are evaluated as simple membership checks and are useful when you want a direct allow or deny rule without creating a separate policy object.

## Create a policy

To create a policy:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**.
4. Select the policy type.
5. Configure the policy-specific settings.
6. Click **Finish**.

If you are not sure which policy type to use, see [Choose a policy type](./index.md#choose-a-policy-type).

## Bind a policy to a flow, stage, application, or source

After creating a policy, bind it to the place where you want the check to apply:

- [flow](../../add-secure-apps/flows-stages/flow/index.md)
- [stage binding](../../add-secure-apps/flows-stages/stages/index.md)
- [application](../../add-secure-apps/applications/index.md)
- [source](../../users-sources/sources/index.md)

:::info Stage Bindings
In authentik, a stage is attached to a flow through a stage binding. When you attach a policy to a stage inside a flow, you are binding the policy to that stage binding, not directly to the stage definition itself. To learn more, see [Bindings](../../add-secure-apps/bindings-overview/index.md).
:::

### Where each binding is evaluated

| Binding target | What it controls                                       |
| -------------- | ------------------------------------------------------ |
| Flow           | Whether the user can start or continue using the flow  |
| Stage binding  | Whether a specific stage runs in that flow             |
| Application    | Whether the user can access the application            |
| Source         | Whether the source can be used for login or enrollment |

### Bind a policy to a flow

Flow bindings control who can use the flow at all.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. In the list of flows, click on the name of the flow to which you want to bind a policy.
4. Click on the **Policy/Group/User Bindings** tab at the top of the page.
5. Either create a new policy and bind it immediately with **Create and bind Policy**, or attach an existing policy, group, or user with **Bind existing policy/group/user**.

### Bind a policy to a stage binding

Stage-binding policies control whether a specific stage runs inside a flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. Open the flow that contains the stage you want to control.
4. Click on the **Stage Bindings** tab at the top of the page.
5. Expand the stage binding for the stage you want to control.
6. Either create and bind a new policy, or bind an existing policy, group, or user.

This is the most common place to use policies for conditional flow behavior. For example:

- only show a CAPTCHA stage when a [Reputation policy](./types/reputation.md) passes
- only show an MFA stage for users who match a policy
- redirect users to different authentication paths with an [Expression policy](./types/expression/index.mdx)

If the policy depends on request data that is only known after the user has interacted with the flow, configure the stage binding to **Evaluate when stage is run** instead of only at planning time.

### Bind a policy to an application

Application bindings control which users, groups, or policy matches can access an application.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**.
3. In the list of applications, click on the name of the application to which you want to bind a policy.
4. Click on the **Policy/Group/User Bindings** tab at the top of the page.
5. Either create and bind a new policy, or bind an existing policy, group, or user.

This is a good fit when you want application access to depend on more than static group membership. For example, you can use a policy to enforce device, network, or contextual requirements before an application appears to the user.

### Bind a policy to a source

Source bindings control who can use a source for login or enrollment.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**.
3. In the list of sources, click on the name of the source to which you want to bind a policy.
4. Click on the **Policy Bindings** tab at the top of the page.
5. Either create and bind a new policy, or bind an existing policy, group, or user.

This is commonly used to limit enrollment or authentication to certain users, groups, or email domains.

## Validate prompt data with policies

Some stages also have their own policy hooks. The most common example is the [Prompt stage](../../add-secure-apps/flows-stages/stages/prompt/index.md), which supports **Validation Policies**.

Use prompt-stage validation policies when the decision depends on data the user has just entered, such as:

- password complexity
- password history
- matching two prompt fields
- validating an email domain during enrollment

Prompt-stage validation is often the right place for [Password](./types/password.md), [Password Uniqueness](./types/password-uniqueness.md), and [Expression](./types/expression/index.mdx) policies.

## How authentik evaluates policies

When a flow, stage binding, application, or source has multiple bindings, authentik evaluates them in order.

### Engine mode: `Any` vs `All`

Every policy binding target has a **Policy engine mode**:

- `Any`: the target passes when any binding passes
- `All`: the target passes only when every binding passes

The default mode is `Any`.

### Order

Bindings are evaluated in ascending order. This matters most when you inspect logs or when you are combining multiple policies that produce end-user messages.

### Enabled bindings only

Disabled bindings are skipped entirely.

### Direct user and group bindings

Bindings to users and groups are evaluated alongside policy bindings:

- a user binding passes when the current user matches
- a group binding passes when the current user is a member of that group

These are a simple way to mix static membership checks with policy-based logic.

### No bindings means pass

If a target has no applicable bindings, authentik treats the result as passing.

## Binding options

Bindings have a few important options beyond the target and order.

### Negate

**Negate** flips the pass or fail result of the binding. This is useful when you want to express "everyone except this group" or turn an allow-style policy into a deny-style rule without copying it.

Negation only changes the boolean result. Any messages returned by the policy are left unchanged.

### Timeout

**Timeout** limits how long authentik will wait for a policy execution before it is terminated. This is especially relevant for expression policies or other policy types that may call external systems.

### Failure result

If a policy errors during execution, **Failure result** decides whether authentik should treat that failure as pass or fail.

Use this carefully:

- fail closed when the policy protects access to something sensitive
- fail open only when availability is more important than enforcement for that specific check

### Execution logging

Individual policies can enable **Execution logging**. When enabled, authentik logs every execution of that policy, not only failures and exceptions. This is helpful while debugging complex access rules.

## Common patterns

### Gate an application with a group or policy

Bind a group directly when the rule is static. Bind a policy when access depends on runtime context such as network, source, prompt data, or request history.

### Run a stage only for some users

Bind a policy to the stage binding, not just to the flow. The stage will only run when that binding passes.

### Validate user input

Attach validation policies directly to the prompt stage when the decision depends on the values the user just entered.
