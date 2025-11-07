---
title: Working with blueprints
---

To learn more about blueprints, what they are and how they are used, executed, and stored, refer to our [Blueprints documentation](./index.mdx).

To learn about exporting configurations (including custom flows) to create a blueprint, read our [Export](./export.mdx) documentation.

To learn how to apply, create, edit, and manage blueprints, refer to the procedures below.

## Apply a blueprint

To _apply_ a blueprint means that the content in the blueprint file is initiated and used by authentik. authentik provides many out-of-the box blueprints, which you can apply either as new [blueprint instance](./index.mdx#blueprint-instance) or as an [imported flow](./index.mdx#imported-flow).

### Add and apply a new blueprint instance

    1. Log in as an administrator to authentik, and open the Admin interface.
    2. In the Admin interface, navigate to **Customization > Blueprints**.
    3. Click **Create** and define the new blueprint instance.
        - **Name**: provide a descriptive name.
        - **Enabled**: toggle on or off. Disabled blueprints cannot be applied.
        - **Blueprint**: select the blueprint upon which you want this new instance to be based. You can select a blueprint file from either a **Local path** (these are part of your authentik installation), an **OCI registry**, or **Internal** (you add the file contents there in the field).
        - **Additional Settings**:
            - **Context**: here you can add any [`key:value` context variable](./index.mdx#blueprint-execution) that you want to use in the blueprint instance.
    4. Click **Create** to save the new blueprint instance. This file is read and applied regularly by authentik.

### Apply a new flow

You can apply a new flow from either the **Flows** page or the **Blueprints** page:

#### Flows page:

1. Log in as an administrator to authentik, and open the Admin interface.
2. In the Admin interface, navigate to **Flows and Stages > Flows**.
3. Click **Import**.
4. In the **Flow** field, select the YAML file for the flow that you want to import. Typically this is a file that you [exported](./export.mdx) and have in your local file system.

#### Blueprints page:

1. Log in as an administrator to authentik, and open the Admin interface.
2. In the Admin interface, navigate to **Customization > Blueprints**.
3. Select the blueprint and click the **Apply** icon under **Actions**.

:::info Download example flows
You can use our [Example flows](../../add-secure-apps/flows-stages/flow/examples/flows.md) and then import them into your authentik instance.
:::

## Edit a blueprint instance or flow

- To edit a blueprint instance, navigate to **Customization > Blueprints** in the Admin interface, select the checkbox in front of the blueprint instance that you want to edit, and then click the Edit icon. Alternatively, you can edit the YAML file directly.

- To edit a flow, navigate to **Customization > Flows** in the Admin interface, and then click **Edit** for the flow that you want to modify.

## Delete a blueprint instance or flow

- To delete a blueprint instance, navigate to **Customization > Blueprints** in the Admin interface, select the checkbox in front of the blueprint instance that you want to delete, and then click **Delete** at the top of the list. You can retrieve and re-apply that blueprint by following the steps to create a new blueperint instance, and selecting that blueprint from the menu list under **Path** on the **Create** page.

- To delete a flow, navigate to **Customization > Flows** in the Admin interface, select the checkbox in front of the flow instance that you want to delete, and then click **Delete** at the top of the list. You can retrieve and re-apply that flow by following the steps above to create a new flow.
