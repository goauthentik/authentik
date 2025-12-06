---
title: Create an Entra ID provider
authentik_enterprise: true
---

For more information about using an Entra ID provider, see the [Overview](./index.md) documentation.

## Prerequisites

To create an Entra ID provider in authentik, you must have already [configured Entra ID](./configure-entra.md).

## Create an Entra ID provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click **Create**.
3. Select **Microsoft Entra Provider** as the provider type, then click **Next**.
4. On the **Create Microsoft Entra Provider** page, set the following configurations:
    - **Name**: provide a descriptive name (e.g. `Entra ID provider`)
    - Under **Protocol settings**:
        - **Client ID**: the Client ID that you copied when [configuring Entra ID](./configure-entra.md)
        - **Client Secret**: the secret from Entra ID
        - **Tenant ID**: the Tenant ID from Entra ID
        - **User deletion action**: determines what authentik will do when a user is deleted from authentik
        - **Group deletion action**: determines what authentik will do when a group is deleted from authentik
    - Under **User filtering**:
        - **Exclude service accounts**: choose whether to include or exclude service accounts
        - **Group**: select a group and only users within that group will be synced to Entra ID
    - Under **Attribute mapping**:
        - **User Property Mappings**: select any property mappings, or use the default
        - **Group Property Mappings**: select any property mappings, or use the default

        :::info Skipping certain users or groups
        The `SkipObject` exception can be used within a property mapping to prevent specific objects from being synced. Refer to the [Provider property mappings documentation](../property-mappings/index.md#skip-objects-during-synchronization) for more details.
        :::

5. Click **Finish**.

### Create an Entra ID application in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications**, click **Create**, and set the following configurations:
    - **Name**: provide a name for the application (e.g. `Entra ID`)
    - **Slug**: enter the name that you want to appear in the URL
    - **Provider**: this field should be left empty
    - **Backchannel Providers**: this field is required for Entra ID. Select the name of the Entra ID provider that you created in the previous section.
    - **UI settings**: leave these fields empty for Entra ID.

3. Click **Create**.
