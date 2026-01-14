---
title: Create a Google Workspace provider
authentik_enterprise: true
---

For more information about using a Google Workspace provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create a Google Workspace provider in authentik, you must have already [configured Google Workspace](./configure-gws.md).

## Create a Google Workspace provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
3. Select **Google Workspace Provider** as the provider type, then click **Next**.
4. On the **Create Google Workspace Provider** page, set the following configurations:
    - **Name**: provide a descriptive name (e.g. `GWS provider`)
    - Under **Protocol settings**:
        - **Credentials**: paste the contents of the JSON file that you downloaded when [configuring Google Workspace](./configure-gws.md)
        - **Delegated Subject**: enter the email address of the Google Workspace user that all authentik actions will be delegated to
        - **Default group email domain**: enter a domain which will be used to generate the email address for groups synced from authentik to Google Workspace
        - **User deletion action**: determines what authentik will do when a user is deleted from authentik
        - **Group deletion action**: determines what authentik will do when a group is deleted from authentik
    - Under **User filtering**:
        - **Exclude service accounts**: choose whether to include or exclude service accounts
        - **Group**: select a group and only users within that group will be synced to Google Workspace
    - Under **Attribute mapping**:
        - **User Property Mappings**: select any property mappings, or use the default
        - **Group Property Mappings**: select any property mappings, or use the default

        :::info Skipping certain users or groups
        The `SkipObject` exception can be used within a property mapping to prevent specific objects from being synced. Refer to the [Provider property mappings documentation](../property-mappings/index.md#skip-objects-during-synchronization) for more details.
        :::

5. Click **Finish**.

## Create a Google Workspace application in authentik

:::info Backchannel Provider
If you have configured the [Google Workspace SAML integration](/integrations/services/google/) to enable authenticating to Google Workspace with authentik, you can add the provider created in the previous section as a backchannel provider to the existing application, instead of creating a new one.
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**, click **Create**, and set the following configurations:
    - **Name**: provide a name for the application (e.g. `GWS`)
    - **Slug**: enter the name that you want to appear in the URL
    - **Provider**: when _not_ used in conjunction with the [Google SAML configuration](/integrations/cloud-providers/google), this should be left empty.
    - **Backchannel Providers**: this field is required for Google Workspace. Select the name of the Google Workspace provider that you created in the previous section.
    - **UI settings**: leave these fields empty for Google Workspace.

3. Click **Create**.
