---
title: Create a SAML provider
---

authentik SAML providers can be created either from scratch or by using SAML metadata exported from the Service Provider (SP). Optionally, the metadata of an authentik SAML provider can be exported back to the SP. Note, however, that many SPs do not support exporting their metadata or importing Identity Provider (IdP) metadata.

## Create a SAML provider and application pair

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **Create with provider**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to solely create the provider by navigating to **Applications** > **Providers** and clicking **Create**.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Applications** and click **Create with provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **SAML Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure SAML Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.

## Create a SAML provider from SP metadata (import SP metadata)

If you have exported SAML metadata from your SP, you can optionally create the authentik SAML provider by importing this metadata.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers** and click **Create** to create a provider.
3. Select **SAML Provider from Metadata** as the **Provider Type**, and then click **Next**.
4. On the **Create SAML Provider from Metadata** page, provide the configuration settings along with an SP metadata file and then click **Finish** to create the provider.
5. (Optional) Edit the created SAML provider and configure any further settings.

## Export authentik SAML provider metadata

After an authentik SAML provider has been created via any of the above methods, you can access its metadata in one of two ways:

### Download authentik metadata

To download the metadata of an authentik SAML provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the name of the provider you want metadata from to open its overview tab.
4. In the **Related objects** section, under **Metadata** click on **Download**. This will download the metadata xml file for that provider.

### Access metadata tab

To view and optionally download the metadata of an authentik SAML provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the name of the provider you want metadata from to open its overview tab.
4. Navigate to the **Metadata** tab.
5. The metadata for the provider will be shown in a codebox. You can optionally use the **Download** button to obtain the metadata as a file.
