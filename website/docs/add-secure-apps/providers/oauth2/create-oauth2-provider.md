---
title: Create an OAuth2 provider
---

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **Create with provider**. We recommend this combined approach for most common use cases. Alternatively, you can use the legacy method to solely create the provider by navigating to **Applications** > **Providers** and clicking **Create**.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications > Applications** and click **Create with provider** to create an application and provider pair.
3. On the **New application** page, define the application settings, and then click **Next**.
4. Select **OAuth2/OIDC** as the **Provider Type**, and then click **Next**.
5. On the **Configure OAuth2/OpenId Provider** page, provide the configuration settings and then click **Submit** to create both the application and the provider.

:::info
Optionally, configure the provider with the `offline_access` scope mapping. By default, applications only receive an access token. To receive a refresh token, applications and authentik must be configured to request the `offline_access` scope. Do this in the Scope mapping area on the **Configure OAuth2/OpenId Provider** page.
:::
