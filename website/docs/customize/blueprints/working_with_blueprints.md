---
title: Working with blueprints
---

To learn more about blueprints and how they are used and stored, refer to our [Blueprints documentation](./index.mdx).

To learn how to create, edit, and manage blueprints, refer to the procedures below.

### Add a new blueprint instance

1. Log in as an administrator to authentik, and open the Admin interface.
2. In the Admin interface, navigate to **Customization > Blueprints**.
3. Click **Create** and define the new blueprint instance.
    - **Name**: provide a descriptive name.
    - **Enabled**: toggle on or off. Disabled blueprints cannot be applied.
    - **Blueprint**: select the blueprint upon which you want this new instance to be based. You can select a blueprint file from either a **Local path** (these are part of your authentik installation), an **OCI registry**, or **Internal** (you add the file contents there in the field).
    - **Additional Settings**:
        - **Context**: here you can add any key:value variable that you want to use in the blueprint instance.
4. Click **Create** to save the new blueprint instance.

### Add a new flow import

I have no idea how...

... also need to cover how to edit one...
