---
title: Policy Bindings and Evaluation
tags:
    - policy
    - bindings
    - access-control
---

For step-by-step instructions on creating and attaching policies, see [Working with policies](./working_with_policies.md). This page focuses on where policy bindings apply, how authentik evaluates them, and which options affect the result.

## Where policies can be bound

:::info Stage Bindings
In authentik, a stage is attached to a flow through a stage binding. When you attach a policy to a stage inside a flow, you are binding the policy to that stage binding, not directly to the stage definition itself. To learn more, see [Bindings](../../add-secure-apps/bindings-overview/index.md).
:::

| Binding target | What it controls                                       | How to configure it                                                                             |
| -------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- |
| Flow           | Whether the user can start or continue using the flow  | [Bind a policy to a flow](./working_with_policies.md#bind-a-policy-to-a-flow)                   |
| Stage binding  | Whether a specific stage runs in that flow             | [Bind a policy to a stage binding](./working_with_policies.md#bind-a-policy-to-a-stage-binding) |
| Application    | Whether the user can access the application            | [Bind a policy to an application](./working_with_policies.md#bind-a-policy-to-an-application)   |
| Source         | Whether the source can be used for login or enrollment | [Bind a policy to a source](./working_with_policies.md#bind-a-policy-to-a-source)               |

In the same binding UI, you can also bind a **user** or **group** directly. Those are evaluated as simple membership checks and are useful when you want a direct allow or deny rule without creating a separate policy object.

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

**Timeout** limits how long authentik will wait for a policy execution before it is terminated. This is especially relevant for expression policies or other policy types that may call external systems. Defaults to 30 seconds.

### Failure result

If a policy errors during execution, **Failure result** decides whether authentik should treat that failure as pass or fail.

Use this carefully:

- fail closed when the policy protects access to something sensitive
- fail open only when availability is more important than enforcement for that specific check

### Execution logging

Individual policies can enable **Execution logging**. When enabled, authentik logs every execution of that policy, not only failures and exceptions. This is helpful while debugging complex access rules.

## Common patterns

### Limit application access with a group or policy

Bind a group directly when the rule is static. Bind a policy when access depends on runtime context such as network, source, prompt data, or request history.

### Run a stage only for some users

Bind a policy to the stage binding, not just to the flow. The stage will only run when that binding passes.

### Validate user input

Attach validation policies directly to the prompt stage when the decision depends on the values the user just entered.
