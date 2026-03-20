---
title: Flow Inspector
---

The Flow Inspector allows administrators to visually determine how custom flows work, inspect the current [flow context](./context/index.mdx) by stepping through the login process and observing the Inspector with each step, and investigate issues.

As shown in the screenshot below, the Flow Inspector displays to the right, beside the selected flow (in this case, "Change Password"), with [information](#flow-inspector-details) about that specific flow and flow context.

![](./flow-inspector.png)

## Access the Flow Inspector

:::info
Be aware that when running a flow with the Inspector enabled, the flow is still executed normally. This means that for example, a [User write](../stages/user_write.md) stage _will_ write user data.
:::

The Inspector is accessible to users that have been granted the [permission](../../../users-sources/access-control/permissions.md) **Can inspect a Flow's execution**, either directly or through a role. Superusers can always inspect flow executions.

### Manually running a flow with the Inspector

1. To access the Inspector, open the Admin interface and navigate to **Flows and Stages > Flows**.

2. Select the specific flow that you want to inspect by clicking its name in the list.

3. On the Flow's detail page, on the left side under **Execute Flow**, click **Use inspector**.

4. The selected flow will launch in a new browser tab, with the Flow Inspector displayed to the right.

### Additional ways to access the Flow Inspector

Alternatively, a user with the correct permission can launch the Inspector by adding the query parameter `?inspector` to the URL after the URL opens on a flow.

Users with permissions to access the Flow Inspector see a button in the top right of the [default flow executor](./executors/if-flow.md) to open the Inspector.

When developing authentik with the debug mode enabled, the Inspector is enabled by default and can be accessed by both unauthenticated users and standard users. However the debug mode should only be used for the development of authentik. So unless you are a developer and need the more verbose error information, the best practice for using the Flow Inspector is to assign the permission, not use debug mode.

:::info Troubleshooting

- If the Flow Inspector does not launch and a "Bad request" error displays, this is likely either because you selected a flow that has a policy bound directly to it that prevents access (so the Inspector won't open because the flow can't be executed) or because you do not have [view permission](../../../users-sources/access-control/manage_permissions.md#view-permissions) on that specific flow.
  :::

### Flow Inspector Details

The following information is shown in the Inspector:

#### Next stage

This is the currently planned next stage. If you have stage bindings configured to `Evaluate when flow is planned`, then you will see the result here. If, however, you have them configured to re-evaluate (`Evaluate when stage is run`), then this will not show up here, since the results will vary based on your input.

Shown is the name and kind of the stage, as well as the unique ID.

#### Plan history

Here you can see an overview of which stages have run, which is currently active, and which is planned to come next. Same caveats as above apply.

#### Current plan context

This shows you the current context. This will contain fields depending on the same, after an identification stage for example you would see "pending_user" defined.

This data is not cleaned, so if your flow involves inputting a password, it will be shown here too.

#### Session ID

The unique ID for the currently used session. This can be used to debug issues with flows restarting/losing state.
