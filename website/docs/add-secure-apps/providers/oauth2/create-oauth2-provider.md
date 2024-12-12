---
title: Create an OAuth2 provider
---

To add a provider (and the application that uses the provider for authentication) use the Application Wizard, which creates both the new application and the required provider at the same time. For typical scenarios, authentik recommends that you use the Wizard to create both the application and the provider together. (Alternatively, use our legacy process: navigate to **Applications --> Providers**, and then click **Create**.)

1. Log into authentik as an admin, and navigate to **Applications --> Applications**.

2. Click **Create with Wizard**.

3. In the **New application** wizard, define the application details, and then click **Next**.

4. Select the **Provider Type** of **OAuth2/OIDC**, and then click **Next**.

5. On the **Configure OAuth2/OpenId Provider** page, provide the configuration settings and then click **Submit** to create and save both the application and the provider.

:::info
Optionally, configure the provider to have the `offline_access` scope mapping. Starting with authentik 2024.2, by default applications only receive an access token. To receive a refresh token, both applications and authentik must be configured to request the `offline_access` scope. Do this in the Scope mapping area on the **Configure OAuth2/OpenId Provider** page.
:::
