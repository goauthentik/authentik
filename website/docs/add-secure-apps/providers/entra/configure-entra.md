---
title: Configure Entra ID
authentik_enterprise: true
---

For more information about using an Entra ID provider, see the [Overview](./index.md) documentation.

Your Entra ID tenant must be configured before you [create a Entra ID provider](./create-entra-provider.md).

This involves creating an app registration, generating a secret, and configuring the required API permissions.

## Configuring you Entra ID tenant

1. Log in to the [Entra ID admin center](https://entra.microsoft.com).
2. Navigate to **App registrations**, click **New registration**, and set the following configurations:
    - Provide a **Name** for the app registration (e.g. `authentik Entra Provider`)
    - Under **Supported account types**, select **Accounts in this organizational directory only**
    - Leave **Redirect URI** empty
3. Click **Register**.
4. On the app detail page, take note of the **Application (client) ID** and **Directory (tenant) ID**. These values will be required when you [create the Entra ID provider](./create-entra-provider.md) in authentik.
5. Next, in the near-left navigation pane, click on **Certificates and Secrets**.
6. On the **Client secrets** tab, click **New client secret** and set the following configuration:
    - Provide a **Description** for the client secret
    - Set an expiry period for the secret. Please note that you will need to rotate the secret value in Entra ID and authentik upon expiry.
7. Click **Add**.
8. The **Value** of the client secret is shown only once. Take note of the value as it will be required when you [create the Entra ID provider](./create-entra-provider.md) in authentik.
9. Next, in the near-left navigation pane, click on **API permissions**.
10. Click **Add a permission** and select **Microsoft Graph** as the API.
11. Select **Application permissions** as the permission type and assign the following permissions:
    - `Group.Create`
    - `Group.ReadWrite.All`
    - `GroupMember.ReadWrite.All`
    - `User.Read`
    - `User.ReadWrite.All`
12. Click **Add permissions**.
13. Under Configured permissions, click **Grant admin consent for default directory**.

Now that you have configured your Entra ID tenant, you are ready to [create an Entra ID provider](./create-entra-provider.md).
