---
title: Working with policies
tags:
    - policy
    - access-control
    - how-to
---

Policies can be built-in policy types or expression policies.

For an overview of the available policy types, see [Policies](./index.md). If you need background on how bindings behave after you attach them, see [Policy bindings and evaluation](./bindings.md).

## Create a policy

To create a policy:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create**.
4. Select the policy type.
5. Configure the policy-specific settings.
6. Click **Finish**.

If you are not sure which policy type to choose, see [Types of policies in authentik](./types/index.mdx).

## Bind a policy to a flow, stage, application, or source

After creating a policy, bind it to the place where you want the check to apply:

- [flow](../../add-secure-apps/flows-stages/flow/index.md)
- [stage binding](../../add-secure-apps/flows-stages/stages/index.md)
- [application](../../add-secure-apps/applications/index.md)
- [source](../../users-sources/sources/index.md)

### Bind a policy to a flow

Flow bindings control who can use the flow at all.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. Open the flow to which you want to bind a policy.
4. Click **Policy/Group/User Bindings**.
5. Either create a new policy and bind it immediately with **Create and bind Policy**, or attach an existing policy, group, or user with **Bind existing policy/group/user**.

### Bind a policy to a stage binding

Stage-binding policies control whether a specific stage runs inside a flow.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. Open the flow that contains the stage you want to control.
4. Click **Stage Bindings**.
5. Expand the stage binding for the stage you want to control.
6. Either create and bind a new policy, or bind an existing policy, group, or user.

If the policy depends on request data that is only known after the user has interacted with the flow, configure the stage binding to **Evaluate when stage is run** instead of only at planning time.

### Bind a policy to an application

Application bindings control which users, groups, or policy matches can access an application.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**.
3. Open the application to which you want to bind a policy.
4. Click **Policy/Group/User Bindings**.
5. Either create and bind a new policy, or bind an existing policy, group, or user.

### Bind a policy to a source

Source bindings control who can use a source for login or enrollment.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**.
3. Open the source to which you want to bind a policy.
4. Click **Policy Bindings**.
5. Either create and bind a new policy, or bind an existing policy, group, or user.

For background on policy ordering, engine mode, and binding options, see [Policy bindings and evaluation](./bindings.md).
