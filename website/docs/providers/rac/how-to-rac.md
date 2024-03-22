---
title: Create a Remote Access (RAC) provider
---

:::info
This feature is in technical preview, so please report any gugs on [GitHub](https://github.com/goauthentik/authentik/issues)
:::

The RAC provider is a highly flexible feature for accessing remote machines. This document provides instructions for the basic creation and configuration of a RAC provider within a defined scenario.

Fow more information about using a RAC provider, see the [Overview](./index.md) documentation. You can also view our [video on YouTube](https://www.youtube.com/watch?v=9wahIBRV6Ts) for setting up a RAC.

## Prereqisites

The RAC provider requires the deployment of the [RAC Outpost](../../outposts/).

## Overview workflow to create a RAC provider

The typcial workflow to create and configure a RAC provider is to 1. create app/provider, 2. create property mappings (that define the access credentials to each remote machine), 3. create an endpoint for each remote machine you want to connect to.

Depending on whether you are connecting using RDP, SSH, or VNC, the exact configuration choices might differ, but the overall workflow applies to all RAC connections.

### Step 1. Create an application and RAC provider

The first step is to create the RAC app and provider.

1. Log in as an admin to authentik, and go to the Admin interface.

2. In the Admin interface, navigate to **Applications -> Applications**.

3. Click **Create with Wizard**. Follow the [instructions](../../applications/manage_apps.md#instructions) to create your RAC application and provider.


### Step 2. Create RAC property mapping

Next, you need to add a property mapping for each of the remote machines you want to access. Property mappings allow you to pass information to external applications, and with RAC they are used to pass the host name, IP address, and access credentials for the remote machines.

1. In the Admin interface, navigate to **Customization -> Property Mappings**.

2. On the **Property Mappings** page, click **Create**.

3. On the **New property mapping** modal, set the following:

    * **Select Type**: RAC Property Mappings
    * **Create RAC Property Mapping**:
        * **Name**s: define a name for the property mapping, perhaps include the type of connection (RDP, SSH, VNC)
        * **General settings**:
            * **Username**: the username for the remote machine
            * **Password**: the password for remote machines
        * **RDP settings**:
            * **Ignore server certificate: select **Enabled** (This setting is required for TRAC to work)
            * **Enable wallpaper**: optional
            * **Enable font smooting**: optional
            * **Enable full window dragging**: optional
        * Advanced settings:
            * **Expressions**: optional, using Python you can define custom [expressions](../../property-mappings/expression.mdx).
4. Click **Finish** to save your settings and close the modal.

### Step 3. Create Endpoints for the Provider

Finally, you need to create an endpoint for each remote machine. Endpoints are defined within providers; connections between the remote machine and authentik are enabled through communication between the provider's endpoint and the remote machine.

1. In the Admin interface navigate to **Applications -> Providers**.

2. Select the RAC provider you created in Step 1 above.

3. On the Provider page, under **Endpoints**, click **Create**.

4. On the **Create Endpoint** modal, provide the following settings:
    * **Name**s: define a name for the endpoint, perhaps include the type of connection (RDP, SSH, VNC)
    * **Protocol**: select the appropriate protocol
    * **Host**: the host name or IP address of the system you are connecting to.
    **Maximum concurrent connections**: select a value or use `-1` to disable the limitation.
    ** Property mapping**: select either the property mapping that you created in Step 2, or use one of the default settings.
    **Advance settings**: optional

5. Click **Create** to save your settings and close the modal.

### Access the remote machine

To verify your configuration and access the remote machine, go to the **User interface** of you authentik instance. On the **My applications** page click the **Remote Access** application to display the defined endpoint(s).

Click the endpoint for the remote machine that you want to access. authentik connects you to a secure shell on the remote machine, in your web browser.







