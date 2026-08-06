---
title: Working with blueprints
---

For an overview of what blueprints are, how they're executed, and where they are stored, see the [Blueprints overview](./index.mdx) documentation.

To export configurations (including custom flows) to create a blueprint, read our [Export](./export.mdx) documentation.

The docs below cover applying, creating, editing, and managing blueprints.

## Apply a blueprint

To _apply_ a blueprint is to have authentik read and execute the contents of a blueprint file. authentik provides many out-of-the-box blueprints, which can be applied either as a [blueprint instance](./index.mdx#blueprint-instance) or as an [imported flow](./index.mdx#imported-flow).

### Create and apply a new blueprint

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Customization** > **Blueprints**.
3. Click **Create** and define the new blueprint instance.
    - **Name**: provide a descriptive name.
    - **Enabled**: toggle on or off. Disabled blueprints cannot be applied.
    - **Blueprint**: select the source for this instance. You can choose a file from a **Local path**, an **OCI registry**, or **Internal** (paste file contents directly, stored in database).
    - **Additional Settings**:
        - **Context**: add any [`key:value` context variable](./index.mdx#blueprint-execution) used in the blueprint instance.
4. Click **Create** to save the new blueprint instance. This file is read and applied regularly by authentik.

### Import and apply a blueprint

You can import and apply a blueprint from either the **Flows** page or the **Blueprints** page. This validates and applies the blueprint immediately, but it does not create a blueprint instance that is monitored or automatically re-applied.

#### Flows page

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Flows and Stages > Flows**, then click **Import**.
3. Choose how to import the blueprint:
    - **File upload**: upload a `.yaml` file from your local file system. Typically this is a downloaded example flow or a file you [exported](./export.mdx).
    - **Local path**: select one of the blueprints available on the authentik server, such as a bundled [example flow](../../add-secure-apps/flows-stages/flow/examples/flows.md).
4. Click **Import**.

#### Blueprints page

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Customization > Blueprints**.
3. Click **Import**.
4. Choose **File upload** to upload a `.yaml` file, or choose **Local path** to select a blueprint available on the authentik server.
5. Click **Import**.

### Apply an existing blueprint

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Customization** > **Blueprints**.
3. Select the blueprint instance from the list.
4. Under **Actions**, click the **Apply** icon.

### Download an example flow, upload it, and apply it

1. Download one of the [example flows](../../add-secure-apps/flows-stages/flow/examples/flows.md).
2. Navigate to **Customization** > **Blueprints** and click **Import**.
3. Choose **File upload**, select the downloaded `.yaml` file, and click **Import**.

## Edit a blueprint instance or flow

- To edit a blueprint instance, navigate to **Customization** > **Blueprints** in the Admin interface and click the **Edit** icon of the instance. Alternatively, edit the YAML file directly.

- To edit a flow, navigate to **Flows and Stages > Flows** in the Admin interface and click **Edit** next to the flow you want to modify.

## Delete a blueprint instance or flow

- To delete a blueprint instance, go to **Customization** > **Blueprints**, select the checkbox next to the instance, and click **Delete**. You can recreate and apply it by creating a new blueprint instance and selecting the file in the **Create** page, under **Path**.

- To delete a flow, navigate to **Flows and Stages** > **Flows**, select the checkbox next to the flow, and click **Delete**. You can re-import the flow later by repeating the import steps in the previous section.
