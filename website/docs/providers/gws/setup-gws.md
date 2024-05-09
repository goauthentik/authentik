---
title: Configure Google Workspace
---

The configuration and set up of your Google Workspace must be done before you add the new provider in authetnik.

:::info
-   note about backchannel provider
:::

## Configure Google Workspace

### Overview of steps

The main steps to set up your Google workspace are as follows:

1. Create your Google Cloud Project
2.
3.
4.

For detailed instructions, refer to Google documentation.

#### Create a Google cloud project
1. Open the Google Cloud Console (https://cloud.google.com/cloud-console).
2. In upper left, click the drop-down box to open the **Select a project** modal box, and then select **New Project**.
3. Use the search bar at the top of your new project page to search for "API Library".
4. On the **API Library** page, use the search bar again to find "Admin SDK API".
5. On the **Admin SDK API** page, click **Enable**.

#### Create credentials

1. After your new Admin SDK API is enabled (it might take a few minutes), return to the Google Cloud console home page (click on **Google Cloud** in upper left).
2. Use the search bar to find and navigate to the **IAM** page.
3. On the **IAM** page, click **Service Accounts** in the left navigation pane.
4. At the top of the **Service Accounts** page, click **Create Service Account**.
*   Under **Service account details** page, define the **Name** and **Description** for the new serice account, and then click **Create and Continue**.
*   Under **Grant this service account access to project** you do not need to define a role, so click **Continue**.
*   Under **Grant users access to project** you do not need to define a role, so click **Done** to complete the creation of the service account.



-   enable Admin SDK API
-   create credentials
-   Select Application data
-   Create key and download json
-   do the `Set up domain-wide delegation for a service account`
    -   Set the scopes to these
    -   `"https://www.googleapis.com/auth/admin.directory.user"`
    -   `"https://www.googleapis.com/auth/admin.directory.group"`
    -   `"https://www.googleapis.com/auth/admin.directory.group.member"`
-   need to get email of an admin user to delegate as?
    -   Not sure which permissions are required
