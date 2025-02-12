---
title: Add an Entra ID provider
---

<span class="badge badge--primary">Enterprise</span>

---

For more information about using an Entra ID provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create an Entra ID provider provider in authentik, you must have already [configured Entra ID](./setup-entra.md) to integrate with authentik. You will need to obtain from Entra three values: the Application (client) ID, the Directory (tenant) ID, and the Client secret. When adding an Entra ID provider in authentik, you must provide these values.

:::info
As detailed in the steps below, when you add an Entra ID provider in authentik you must define the **Backchannel provider** using the name of the Entra ID provider that you created in authentik. If you have also configured Entra ID to log in using authentik, then this configuration can be done on the same app.
:::

### Create the Entra ID provider in authentik

1.  Log in as an admin to authentik, and go to the Admin interface.
2.  In the Admin interface, navigate to **Applications -> Providers**.
3.  Click **Create**, and in the **New provider** modal box select **Microsoft Entra Provider** as the type and click **Next**.
4.  Define the following fields:

    - **Name**: define a descriptive name, such as "Entra provider".

    - **Protocol settings**

        - **Client ID**: enter the Client ID that you [copied from your Entra app](./setup-entra.md).
        - **Client Secret**: enter the secret from Entra.
        - **Tenant ID**: enter the Tenant ID from Entra.
        - **User deletion action**: determines what authentik will do when a user is deleted from the Entra ID system.
        - **Group deletion action**: determines what authentik will do when a group is deleted from the Entra ID system.

    **User filtering**

        - **Exclude service accounts**: set whether to include or exclude service accounts.
        - **Group**: select any specific groups to enforce that filtering (for all actions) is done only for the selected groups.

    **Attribute mapping**

        - **User Property Mappings**: select any applicable mappings, or use the default.
        - **Group Property Mappings**: select any applicable mappings, or use the default.

5.  Click **Finish**.

### Create an Entra ID application in authentik

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Applications -> Applications**.
3. Click **Create**, and in the **Create Application** modal box define the following fields:

    - **Name**: provide a descriptive name.
    - **Slug**: enter the name of the app as you want it to appear in the URL.
    - **Group**: optionally, chose a group; apps in the same group are displayed together on the **My applications** page.
    - **Provider**: when _not_ used in conjunction with the Entra ID SAML configuration this field should be left empty.
    - **Backchannel Providers**: this field is required for Entra ID. Select the name of the Entra ID provider that you created in the steps above.
    - **Policy engine mode**: select **any** or **all** to set your policy mode.
    - **UI settings**: leave these fields empty for Entra ID.

4. Click **Create**.
