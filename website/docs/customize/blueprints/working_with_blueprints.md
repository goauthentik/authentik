---
title: Working with blueprints
---

To learn more about blueprints, what they are and how they are used, executed, and stored, refer to our [Blueprints documentation](./index.mdx).

To learn about exporting configurations to create a blueprint, read our [Export](./export.mdx) documentation.

To learn how to apply, create, edit, and manage blueprints, refer to the procedures below.

### Apply an existing blueprint

authentik provides many out-of-the box blueprints, which you can apply either as new [blueprint instance](./index.mdx#blueprint-instance) or as an [imported flow](./index.mdx#imported-flow).

#### Apply a new flow

You can apply a new flow from either the **Flows** page or the **Blueprints** page:

- Flows page:
    1. Log in as an administrator to authentik, and open the Admin interface.
    2. In the Admin interface, navigate to **Flows and Stages > Flows**.
    3. Click **Import**.
    4. In the **Flow** field, select the YAML file for the flow that you want to import. Typically this is a file that you [exported](./export.mdx) and have n your local file system.

- Blueprints page:
    1. Log in as an administrator to authentik, and open the Admin interface.
    2. In the Admin interface, navigate to **Customization > Blueprints**.
    3. Select the blueprint and click the **Apply** icon under **Actions**.

#### Add a new blueprint instance

    1. Log in as an administrator to authentik, and open the Admin interface.
    2. In the Admin interface, navigate to **Customization > Blueprints**.
    3. Click **Create** and define the new blueprint instance.
        - **Name**: provide a descriptive name.
        - **Enabled**: toggle on or off. Disabled blueprints cannot be applied.
        - **Blueprint**: select the blueprint upon which you want this new instance to be based. You can select a blueprint file from either a **Local path** (these are part of your authentik installation), an **OCI registry**, or **Internal** (you add the file contents there in the field).
        - **Additional Settings**:
            - **Context**: here you can add any `key:value` variable that you want to use in the blueprint instance.
    4. Click **Create** to save the new blueprint instance.

### Edit a blueprint instance or flow

- To edit a blueprint instance, navigate to **Customization > Blueprints** in the Admin interface, select the checkbox in front of the blueprint instance that you want to edit, and then click the Edit icon.

- To edit a flow, refer to our [Flows documentation](../../add-secure-apps/flows-stages/flow/index.md).

### Delete a blueprint instance or flow

- To delete a blueprint instance, navigate to **Customization > Blueprints** in the Admin interface, select the checkbox in front of the blueprint instance that you want to edit, and then click **Delete** at the top of the list.

??? what are all the procedurals? - create a new blueprint instance (use Create button) - apply an existing blueprint (instance, so it is used at startup) OR import a flow's blueprint (only read once). - edit or delete a bp instance (edit the name, enabled, contenxt) and ALSO editing the yaml file. - delete a flow import blueprint (on the list of blueprints, if deleted how to get it back?) - export a flow as a blueprint (already documented)
