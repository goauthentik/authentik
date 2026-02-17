---
title: Create a Remote Access Control (RAC) provider
---

For an overview of Remote Access Control (RAC), see the [RAC provider](./index.md) documentation.

You can also watch our video on YouTube for setting up RAC:

<iframe width="560" height="315" src="https://www.youtube.com/embed/9wahIBRV6Ts?start=22" title="YouTube video player" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen></iframe>

## Workflow to create an RAC provider

Follow this workflow to create and configure an RAC provider:

1. Create a RAC provider and application pair.
2. Create RAC property mappings (that define the access credentials to each remote machine).
3. Create endpoints for each remote machine you want to connect to.
4. Create an RAC outpost to service the provider.

Depending on whether you are connecting using RDP, SSH, or VNC, the exact configuration choices will differ, but the overall workflow applies to all RAC connections.

### Create a RAC provider and application pair

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **Create with Provider**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to create only the provider by navigating to **Applications** > **Providers** and clicking **Create**.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select the **RAC** provider type, and then click **Next**.
5. On the **Configure Remote Access Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.

### Create RAC property mappings

Next, you need to add property mappings for each remote machine you want to access. RAC property mappings can be used to pass the access credentials and connection settings of the remote machine.

Refer to the [RAC Credentials Prompt](./rac_credentials_prompt.md) and [RAC SSH Public Key Authentication](./rac-public-key.md) documentation for alternative methods of handling RAC authentication.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings**, and click **Create**.
3. Select **RAC Provider Property Mapping** as the property mapping type, and then click **Next**.
4. On the **Create RAC Provider Property Mapping** page, provide the following configuration settings:
    - **Name**: provide a name for the property mapping
    - Under **General settings**:
        - **Username**: the username for the remote machine
        - **Password**: the password for the remote machine
    - Under **Advanced settings**:
        - **Expression _(optional)_**: define other connection settings to be used, such as an SSH key. For more information, refer to the [Connection settings](./index.md#connection-settings) documentation.

5. Click **Finish**.

### Create endpoints for the provider

Then, you need to create an endpoint corresponding to each remote machine you want to connect to. Endpoints define the IP address, port, protocol, and other settings used for connecting to a remote machine.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the **Edit** button on the RAC provider that you previously created.
4. On the Provider page, under **Endpoints**, click **Create**, and provide the following settings:
    - **Provider Name** (endpoint name): define a name for the endpoint
    - **Protocol**: select the appropriate protocol
    - **Host**: enter the host name or IP address of the remote machine. Optionally include the port.
    - **Maximum concurrent connections**: select a value or use `-1` to disable the limitation
    - **Property mappings**: select either the property mapping that you previously created, or use one of the default RAC property mappings
    - **Advanced settings _(optional)_**: define other connection settings to be used. For more information, refer to the [Connection settings](./index.md#connection-settings) documentation

5. Click **Create**.

### Create an RAC outpost

The RAC provider requires the deployment of an [RAC Outpost](../../outposts/index.mdx).

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**.
3. Click **Create** and set the following values:
    - **Name**: define a name for the outpost.
    - **Type**: `RAC`
    - **Integration**: select either Docker or Kubernetes, or optionally [manually deploy the outpost](../../outposts/index.mdx#outpost-integrations).
    - **Applications**: select the RAC application that you previously created.
    - **Advanced settings _(optional)_**: for further optional configuration settings, refer to [RAC Configuration](../../outposts/index.mdx#configuration).

4. Click **Create** to save your new outpost.

## Access the remote machine

To verify your configuration and access the remote machine, go to the **User interface** of your authentik instance. On the **My applications** page, click the **Remote Access** application to start a secure session on the remote machine in your web browser.

If you defined multiple endpoints, click the endpoint for the remote machine that you want to access.
