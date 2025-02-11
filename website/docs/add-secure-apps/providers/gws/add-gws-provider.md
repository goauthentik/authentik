---
title: Create a Google Workspace provider
---

<span class="badge badge--primary">Enterprise</span>

---

For more information about using a Google Workspace provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create a Google Workspace provider in authentik, you must have already [configured Google Workspace](./setup-gws.md) to integrate with authentik.

:::info
When adding the Google Workspace provider in authentik, you must define the **Backchannel provider** using the name of the Google Workspace provider that you created in authentik. If you have also configured Google Workspace to log in using authentik following [these](../../../../integrations/services/google/), then this configuration can be done on the same app.
:::

### Create the Google Workspace provider in authentik

1. Log in as an admin to authentik, and go to the Admin interface.

2. In the Admin interface, navigate to **Applications -> Providers**.

3. Click **Create**, and select **Google Workspace Provider**, and in the **New provider** modal box, define the following fields:

    - **Name**: define a descriptive name, such as "GWS provider".

    - **Protocol settings**

        - **Credentials**: paste the contents of the JSON file you downloaded earlier.
        - **Delegated Subject**: enter the email address of the user all of authentik's actions should be delegated to
        - **Default group email domain**: enter a default domain which will be used to generate the domain for groups synced from authentik.
        - **User deletion action**: determines what authentik will do when a user is deleted from authentik.
        - **Group deletion action**: determines what authentik will do when a group is deleted from authentik.

    - **User filtering**

        - **Exclude service accounts**: set whether to include or exclude service accounts.
        - **Group**: select any specific groups to enforce that filtering (for all actions) is done only for the selected groups.

    - **Attribute mapping**

        - **User Property Mappings**: select any applicable mappings, or use the default.
        - **Group Property Mappings**: select any applicable mappings, or use the default.

4. Click **Finish**.

### Create a Google Workspace application in authentik

1. Log in as an admin to authentik, and go to the Admin interface.
2. In the Admin interface, navigate to **Applications -> Applications**.
   :::info
   If you have also configured Google Workspace to log in using authentik following [these](https://docs.goauthentik.io/integrations/services/google/index), then this configuration can be done on the same app by adding this new provider as a backchannel provider on the existing app instead of creating a new app.
   :::
3. Click **Create**, and in the **New provider** modal box, and define the following fields:

    - **Slug**: enter the name of the app as you want it to appear in the URL.
    - **Provider**: when _not_ used in conjunction with the Google SAML configuration should be left empty.
    - **Backchannel Providers**: this field is required for Google Workspace. Select the name of the Google Workspace provider that you created in the steps above.
    - **UI settings**: leave these fields empty for Google Workspace.

4. Click **Finish**.
