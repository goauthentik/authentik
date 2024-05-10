---
title: Create a Google Workspace provider
---

<span class="badge badge--primary">Enterprise</span>

---

:::info
This feature is in technical preview, so please report any bugs on [GitHub](https://github.com/goauthentik/authentik/issues).
:::



For more information about using a Google Workspace provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create a Google Workspace provider in authentik, you must have already [configured Google Workspace](./setup-gws.md) to integrate with authentik.

:::info
When adding the Google Workspace provider in authentik, you must define the **Backchannel provider** using the name of the Google Workspace provider that you created in authentik. Do NOT add any value in the **Provider** field (doing so will cause the provider to display as an application on the user interface, under **My apps**, which is not supported for Google Workspace).
:::

### Create the Google Workspace provider in authentik

1. Log in as an admin to authentik, and go to the Admin interface.

2. In the Admin interface, navigate to **Applications -> Providers**.

3. Click **Create**, and in the **New provider** modal box, define the following fields:

    - **Name**: define a descriptive name, such as "GWS provider".

        **Protocol settings**

        - **Client ID**: enter the Client ID that you [copied from your Google Workspace](./setup-gws.md).
        - **Client Secret**: enter the secret from Google Workspace.
        - **Tenant ID**: enter the Tenant ID from Google Workspace.
        - **User deletion action**: determines what authentik will do when a user is deleted from the Google Workspace system.
        - **Group deletion action**: determines what authentik will do when a group is deleted from the Google Workspace system.

        **User filtering**

        - **Exclude service accounts**: set whether to include or exclude service accounts.
        - **Group**: select any specific groups to enforce that filtering (for all actions) is done only for the selected groups.

        **Attribute mapping**

        - **User Property Mappings**: select any applicable mappings, or use the default.
        - **Group Property Mappings**: select any applicable mappings, or use the default.

4. Click **Finish**.

### Create a Google Workspace application in authentik

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Applications -> Applications**.
3. Click **Create**, and in the **New provider** modal box, and define the following fields:

    - **Slug**: enter the name of the app as you want it to appear in the URL.
    - **Group**: optionally, enter a group name, of you want this new application to be grouped with other similar apps.
    - **Provider**: _leave this field empty_. For certain types of providers (Google Workspace, Entra ID, and SCIM, for example), a paired application is not needed.
    - **Backchannel Providers**: this field is required for Google Workspace. Select the name of the Google Workspace provider that you created in the steps above.
    - **Policy engine mode**: select **any** or **a*ll** to set your policy mode.
    - **UI settings**: leave these fields empty for Google Workspace.

4. Click **Finish**.
