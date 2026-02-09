---
title: Create a WS-Fed provider
---

An authentik WS-Fed provider can be created either from scratch or by using for a WS-Fed provider [metadata](#create-a-ws-fed-provider-from-sp-metadata-import-sp-metadata) exported from the Security Token Service (STS).

## Create a WS-Fed provider and application pair

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **Create with provider**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to solely create the provider by navigating to **Applications** > **Providers** and clicking **Create**.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Applications** and click **Create with provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **WS-Fed Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure WS-Fed Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.
    - **Reply URL**: Enter the Application Callback URL (the applications's Assertion Consumer Service URL) where the token should be sent.

## Create a WS-Fed provider from SP metadata (import SP metadata)

If you have exported WS-Fed metadata from your SP, you can optionally create the authentik WS-Fed provider by importing this metadata.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers** and click **Create** to create a provider.
3. Select **WS-Fed Provider from Metadata** as the **Provider Type**, and then click **Next**.
4. On the **Create WS-Fed Provider from Metadata** page, provide the configuration settings along with an SP metadata file and then click **Finish** to create the provider.
5. (Optional) Edit the created WS-Fed provider and configure any further settings.

## Export authentik WS-Fed provider metadata

After an authentik WS-Fed provider has been created via any of the above methods, you can access its metadata in one of two ways:

### Download authentik metadata for a WS-Fed provider

To download the metadata of an authentik WS-Fed provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the name of the provider you want metadata from. to open its overview tab.
4. On the **Overview** tab, in the **Related objects** section, click on **Download** under **Metadata**. This will download the metadata XML file for that provider.

### Access metadata tab for a WS-Fed provider

To view and optionally download the metadata of an authentik WS-Fed provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the name of the provider you want metadata from to open its overview tab.
4. Navigate to the **Metadata** tab.
5. The metadata for the provider will be shown in a codebox. You can optionally use the **Download** button to obtain the metadata as a file.
