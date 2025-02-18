---
title: Create an SSF provider
---

To add a provider (and the application that uses the provider for authentication) use the **Create with provider** feature, which creates both the new application and the required provider at the same time. For typical scenarios, authentik recommends that you create both the application and the provider together. (Alternatively, you can use our legacy process to first create the provider and then the application.)

1. Log into authentik as an admin, and in the Admin interface navigate to **Applications --> Applications**.

2. Click **Create with provider**.

3. In the modal, define the application details, and then click **Next**.

4. Select the **Provider Type** of **SSF**, and then click **Next**.

5. On the **Configure SSF Provider** page, provide the configuration settings.

    - Be sure to select a **Signing Key**.

6. Click **Submit** to create and save both the application and the provider.
