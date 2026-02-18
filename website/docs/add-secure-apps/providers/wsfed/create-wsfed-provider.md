---
title: Create a WS-Federation provider
---

An authentik WS-Federation provider is typically created as part of an application/provider pair, using the steps below. You can also create a standalone provider, and then later assign an application to use it.

## Create a WS-Federation provider and application pair

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Applications** and click **Create with provider** to create an application and provider pair.
3. On the **New application** page, define the application details, and then click **Next**.
4. Select **WS-Federation Provider** as the **Provider Type**, and then click **Next**.
5. On the **Configure WS-Federation Provider** page, provide a name for the provider, select an authorization flow, and the two required configuration settings:
    - **Reply URL**: Enter the application callback URL, where the token should be sent. This is the specific endpoint on an RP (application) where an Identity Provider (STS) sends the security token and authentication response after a successful log in.
    - **Realm**: Enter the identifier (string) of the requesting realm; that is, the Relying Party (RP) or application receiving the token. Realm is similar to the SAML 2.0 Entity ID.
6. Click **Submit** to create both the application and the provider.

## Export authentik WS-Federation provider metadata

After an authentik WS-Federation provider has been created via any of the above methods, you can access its metadata in one of two ways:

### Download authentik metadata for a WS-Federation provider

To download the metadata of an authentik WS-Federation provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the name of the provider you want metadata for.
4. On the **Overview** tab, in the **Related objects** section, click on **Download** under **Metadata**. This will download the metadata XML file for that provider.

### Access the Metadata tab for a WS-Federation provider

To view and optionally download the metadata of an authentik WS-Federation provider, follow these steps:

1. Log in to authentik as an administrator, and open the authentik Admin interface.
2. Navigate to **Applications > Providers**.
3. Click the name of the provider you want metadata for, and then click the **Metadata** tab.
4. The metadata for the provider will be shown in a code box. You can optionally use the **Download** button to obtain the metadata as a file.
