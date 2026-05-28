---
title: Create an OAuth2 provider
---

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** > **Applications** and click **New Application**. We recommend this combined approach for most common use cases. (Alternatively, you can first create only the provider and then later pair it with an application, by navigating to **Applications** > **Providers** and clicking **New Provider**.)

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications > Applications** and click **New Application** to create an application and provider pair.
3. On the **New application** page, define the application settings, and then click **Next**.
4. Select **OAuth2/OIDC** as the **Provider Type**, and then click **Next**.
5. On the **Configure Provider** page, provide the required configuration settings.
6. Click **Create Application** to create both the application and the provider.

:::info
Optionally, configure the provider with the `offline_access` scope mapping. By default, applications only receive an access token. To receive a refresh token, applications and authentik must be configured to request the `offline_access` scope. Do this in the Scope mapping area on the **Configure OAuth2/OpenID Provider** page.
:::
