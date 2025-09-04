---
title: Create a SAML provider
---

## Create a SAML provider and application pair

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **Create with provider**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to solely create the provider by navigating to **Applications** > **Providers** and clicking **Create**.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Applications** and click **Create with provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **SAML Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure SAML Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.

## Create a SAML provider

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers** and click **Create** to create a provider.
3. Select **SAML Provider** as the **Provider Type**, and then click **Next**.
4. On the **Create SAML Provider** page, provide the configuration settings and then click **Submit** to create the provider.

## Create a SAML provider from SP metadata

If you have exported SAML metadata from your SP, you can optionally create the authentik SAML provider by importing this metadata.

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers** and click **Create** to create a provider.
3. Select **SAML Provider from Metadata** as the **Provider Type**, and then click **Next**.
4. On the **Create SAML Provider from Metadata** page, provide the configuration settings along with an SP metadata file and then click **Finish** to create the provider.
5. (Optional) Edit the created SAML provider and configure any further settings.

## Export authentik SAML provider metadata

Once an authentik SAML provider has been created via any of the above methods, you can export its metadata in one of two ways:

### Metadata download

### Metadata tab
