---
title: Create a SAML provider
---

To create a provider along with the corresponding application that uses it for authentication, navigate to **Applications** → **Applications** and click **Create with provider**. We recommend this combined approach for most common use cases. Alternatively, you can follow the legacy method by navigating to **Applications** → **Providers** and clicking **Create**.

1. Log in to authentik as an administrator, and open the authentik Admin interface.

2. Navigate to **Applications -> Applications** and click **Create with provider** to create an application and provider pair.

3. In the **New application** box, define the application details, and then click **Next**.

4. Select the **Provider Type** of either **SAML Provider**, and then click **Next**.
    - TODO: talk about the diff bwetween using metadata vs not...

5. On the **Configure SAML Provider** page, provide the configuration settings and then click **Submit** to create and save both the application and the provider.

TODO describe each field.... maybe. There are some very important fields under Advanced Protocol settings...
