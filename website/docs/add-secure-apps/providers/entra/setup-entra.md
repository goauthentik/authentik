---
title: Configure Entra ID
authentik_enterprise: true
---

The configuration of your Microsoft Entra ID environment must be completed before you [add the new provider](./add-entra-provider.md) in authentik.

For detailed instructions, refer to Microsoft Entra ID documentation.

## Configure Entra ID

1. Log into the Azure portal and on the Home page, under Azure services, click on or search for **App registrations**.
2. On the **App registrations** page, click **New registration**.
3. On the **Register an application** page, define the **Name** of the app, and under **Supported account types** select **Accounts in this organizational directory only**. Leave **Redirect URI** empty.
4. Click **Register**.
   The app's detail page displays.
5. On the app detail page, copy both the **Application (client) ID** and the **Directory (tenant) ID** values and store in a temporary place. These values will be needed when you [create the Entra ID provider](./add-entra-provider.md) in authentik.
6. Next, click on **Certificates and Secrets** in the near-left navigation pane and create a new secret.
7. On the **Certificates and Secrets** page, on the **Client secrets** tab, copy the **Value** of the secret and store it in a temporary place. Like with the client ID and the tenant ID, this secret will be needed when you [create the Entra ID provider](./add-entra-provider.md) in authentik.
8. Next, click on **API permissions** in the near-left navigation pane.
9. Click on **Add a permission** and add the following permissions by selecting **Microsoft Graph** and then **Application Permissions**:
    - `Group.Create`
    - `Group.ReadWrite.All`
    - `GroupMember.ReadWrite.All`
    - `User.Read`
    - `User.ReadWrite.All`

Now you are ready to [add Entra ID as a provider](./add-entra-provider.md) in authentik.
