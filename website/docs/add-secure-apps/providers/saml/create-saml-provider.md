---
title: Create a SAML provider
---

To add a provider (and the application that uses the provider for authentication) use the ** Create with provider** option, which creates both the new application and the required provider at the same time. For typical scenarios, authentik recommends that you create both the application and the provider together. (Alternatively, use our legacy process: navigate to **Applications --> Providers**, and then click **Create**.)

1. Log in to authentik as an admin, and open the authentik Admin interface.

2. Navigate to **Applications -> Applications** and click **Create with provider** to create an application and provider pair.

3. In the **New application** box, define the application details, and then click **Next**.

4. Select the **Provider Type** of **SAML**, and then click **Next**.

5. On the **Configure SAML Provider** page, provide the configuration settings and then click **Submit** to create and save both the application and the provider.
