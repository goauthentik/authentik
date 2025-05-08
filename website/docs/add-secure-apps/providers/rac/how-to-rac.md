---
title: Create a Remote Access Control (RAC) provider
---

## Introduction

The RAC provider is a highly flexible feature for accessing remote machines.

For overview information, see the [Remote Access Control (RAC) Provider](./index.md) documentation. You can also view our video on YouTube for setting up RAC.

<iframe width="560" height="315" src="https://www.youtube.com/embed/9wahIBRV6Ts;start=22" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Prerequisites

The RAC provider requires the deployment of the [RAC Outpost](../../outposts/index.mdx).

## Overview workflow to create an RAC provider

The typical workflow to create and configure a RAC provider is:

1. Create an application and provider.
2. Create property mappings (that define the access credentials to each remote machine).
3. Create an endpoint for each remote machine you want to connect to.

Depending on whether you are connecting using RDP, SSH, or VNC, the exact configuration choices will differ, but the overall workflow applies to all RAC connections.

### Create an application and RAC provider

The first step is to create the RAC application and provider.

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with provider**.
3. Follow these [instructions](../../applications/manage_apps.mdx#instructions) to create your RAC application and provider.

### Create RAC property mappings

Next, you need to add property mappings for each remote machine you want to access. Property mappings allow you to pass information to external applications, and with RAC they are used to pass the host name, IP address, and access credentials of the remote machine.

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization > Property Mappings** and click **Create**.

    - **Select Type**: RAC Property Mappings
    - **Create RAC Property Mapping**:
        - **Name**s: define a name for the property mapping, perhaps include the type of connection (RDP, SSH, VNC)
        - **General settings**:
            - **Username**: the username for the remote machine
            - **Password**: the password for the remote machine
        - **RDP settings**:
            - **Ignore server certificate**: select **Enabled** (Depending on the setup of your RDP Server, it might be required to enable this setting)
            - **Enable wallpaper**: optional
            - **Enable font smoothing**: optional
            - **Enable full window dragging**: optional
        - Advanced settings:
            - **Expressions**: optional, using Python you can define custom [expressions](../property-mappings/expression.mdx).

3. Click **Finish**.

### Create Endpoints for the Provider

Finally, you need to create an endpoint for each remote machine. Endpoints are defined within providers; connections between the remote machine and authentik are enabled through communication between the provider's endpoint and the remote machine.

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the **Edit** button on the RAC provider that you previously created.
4. On the Provider page, under **Endpoints**, click **Create**, and provide the following settings:

    - **Name**: define a name for the endpoint, perhaps include the type of connection (RDP, SSH, VNC)
    - **Protocol**: select the appropriate protocol
    - **Host**: the host name or IP address of the remote machine
    - **Maximum concurrent connections**: select a value or use `-1` to disable the limitation
    - **Property mapping**: select either the property mapping that you previously created, or use one of the default settings
    - **Advance settings**: optional

5. Click **Create**.

### Access the remote machine

To verify your configuration and access the remote machine, go to the **User interface** of your authentik instance. On the **My applications** page click the **Remote Access** application and authentik will connect you to a secure session on the remote machine, in your web browser.

If you defined multiple endpoints, click the endpoint for the remote machine that you want to access.
