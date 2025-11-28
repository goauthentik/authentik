---
title: Plex
tags:
    - source
    - plex
---

Allows users to authenticate using their Plex credentials by configuring Plex as a federated identity provider via OAuth2.

## Preparation

None

## authentik configuration

To support the integration of Plex with authentik, you need to create a Plex source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Plex Source** as the source type.
    - **Create Plex Source**: provide a name, a slug, and set the following required configurations:
        - **Protocol settings**
            - **Client ID**: Set a unique Client ID or leave the generated ID
                - Click **Load Servers** to login to Plex and pick the authorized Plex Servers for "allowed users".
                - Decide if _anyone_ with a Plex account can authenticate or only friends you share access with.
3. Click **Finish** to save your settings.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.
