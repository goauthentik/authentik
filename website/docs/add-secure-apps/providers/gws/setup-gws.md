---
title: Configure Google Workspace
authentik_enterprise: true
---

The configuration and set up of your Google Workspace must be completed before you [add the new provider](./add-gws-provider.md) in authentik.

## Overview of steps

The main steps to set up your Google workspace are as follows:

1. [Create your Google Cloud Project](#create-a-google-cloud-project)
2. [Create a service account](#create-a-service-account)
3. [Set credentials for the service account](#set-credentials-for-the-service-account)
4. [Define access and scope in the Admin Console](#set-credentials-for-the-service-account)
5. [Select email address for the Delegated Subject](#select-email-address-for-the-delegated-subject)

For detailed instructions, refer to Google documentation.

### Create a Google cloud project

1. Open the Google Cloud Console (https://cloud.google.com/cloud-console).
2. In upper left, click the drop-down box to open the **Select a project** box, and then select **New Project**.
3. Create a new project and give it a name like "authentik GWS"
4. Use the search bar at the top of your new project page to search for "API Library".
5. On the **API Library** page, use the search bar again to find "Admin SDK API".
6. On the **Admin SDK API** page, click **Enable**.

### Create a service account

1. After the new Admin SDK API is enabled (it might take a few minutes), return to the Google Cloud console home page (click on **Google Cloud** in upper left).
2. Use the search bar to find and navigate to the **IAM** page.
3. On the **IAM** page, click **Service Accounts** in the left navigation pane.
4. At the top of the **Service Accounts** page, click **Create Service Account**.

- Under **Service account details** page, define the **Name** and **Description** for the new service account, and then click **Create and Continue**.
- Under **Grant this service account access to project** you do not need to define a role, so click **Continue**.
- Under **Grant users access to project** you do not need to define a role, so click **Done** to complete the creation of the service account.

### Set credentials for the service account

1. On the **Service accounts** page, click the account that you just created.
2. Click the **Keys** tab at top of the page, the click **Add Key -> Create new key**.
3. In the Create box, select JSON as the key type, and then click **Create**.
   A pop-up displays with the private key, and the key is saved to your computer as a JSON file.
   Later, when you create your authentik provider for Google Workspace, you will add this key in the **Credentials** field.
4. On the service account page, click the **Details** tab, and expand the **Advanced settings** area.
5. Copy the **Client ID** (under **Domain-wide delegation**), and then click **View Google Workspace Admin Console**.
6. Log in to the Admin Console, and then navigate to **Security -> Access and data control -> API controls**.
7. On the **API controls** page, click **Manage Domain Wide Delegation**.
8. On the **Domain Wide Delegation** page, click **Add new**.
9. In the **Add a new client ID** box, paste in the Client ID that you copied from the Admin console earlier (the value from the downloaded JSON file) and paste in the following scope documents:
    - `https://www.googleapis.com/auth/admin.directory.user`
    - `https://www.googleapis.com/auth/admin.directory.group`
    - `https://www.googleapis.com/auth/admin.directory.group.member`
    - `https://www.googleapis.com/auth/admin.directory.domain.readonly`

### Select email address for the Delegated Subject

The Delegated Subject email address is a required field when creating the provider in authentik.

1. Open to the main Admin console page, and navigate to **Directory -> Users**.
2. You can either select an existing user's email address or **Add new user** and define the user and email address to use as the Delegated Subject.
3. Save this email address to enter into authentik when you are creating the Google Workspace provider.

Now that you have configured your Google Workspace, you are ready to [add it as a provider in authentik](./add-gws-provider.md).
