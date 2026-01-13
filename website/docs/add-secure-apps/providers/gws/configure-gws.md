---
title: Configure Google Workspace
authentik_enterprise: true
---

For more information about using a Google Workspace provider, see the [Overview](./index.md) documentation.

Your Google Workspace organization must be configured before you [create a Google Workspace provider](./create-gws-provider.md).

## Configure your Google Workspace Organization

The main steps to configure your Google Workspace organization are:

1. [Create a Google Cloud project](#create-a-google-cloud-project)
2. [Create a service account](#create-a-service-account)
3. [Configure service account key and scopes](#configure-service-account-key-and-scopes)
4. [Select a user for the Delegated Subject](#select-a-user-for-the-delegated-subject)

### Create a Google Cloud project

1. Open the [Google Cloud console](https://cloud.google.com/cloud-console).
2. In the upper left, click the drop-down box to open the **Select a project** box, then select **New Project**.
3. Create a new project and provide a name (e.g. `authentik GWS`).
4. Use the search bar at the top of your new project page to search for `API Library`.
5. On the **API Library** page, use the search bar again to find `Admin SDK API`.
6. On the **Admin SDK API** page, click **Enable**.

### Create a service account

1. After the new Admin SDK API is enabled (it might take a few minutes), return to the Google Cloud console home page by clicking on **Google Cloud** in the upper left.
2. Use the search bar to find and navigate to the **IAM** page.
3. On the **IAM** page, click **Service Accounts** in the left navigation pane.
4. At the top of the **Service Accounts** page, click **Create Service Account**.
    - Under **Service account details** page, define the **Name** and **Description** for the new service account, then click **Create and Continue**.
    - Under **Grant this service account access to project** you do not need to define a role, so click **Continue**.
    - Under **Grant users access to project** you do not need to define a role, so click **Done** to complete the creation of the service account.

### Configure service account key and scopes

1. On the **Service accounts** page, click the account that you just created.
2. Click the **Keys** tab at top of the page, then click **Add Key** > **Create new key**.
3. Select **JSON** as the key type, then click **Create**.
   A pop-up displays with the private key. The key can be saved to your computer as a JSON file. This key will be required when creating the Google Workspace provider in authentik.

    :::info Allow key creation
    By default, the Google Cloud organization policy `iam.disableSerivceAccountKeyCreation` prevents creating service account keys. To allow key creation:
    1. Navigate to **IAM & Admin** > **Organization Policies** and select the **Disable service account key creation** policy.
    2. Click **Manage policy** and disable the policy.
    3. Click **Set policy** to save your changes.
       :::

4. On the service account page, click the **Details** tab, and expand the **Advanced settings** area.
5. Copy the **Client ID** (under **Domain-wide delegation**), and then click **View Google Workspace Admin Console**.
6. Log in to the Admin Console, and then navigate to **Security** > **Access and data control** > **API controls**.
7. On the **API controls** page, click **Manage Domain Wide Delegation**.
8. On the **Domain Wide Delegation** page, click **Add new**.
9. In the **Add a new client ID** box, paste in the Client ID that you copied from the Admin console earlier (the value from the downloaded JSON file) and paste in the following scope documents:
    - `https://www.googleapis.com/auth/admin.directory.user`
    - `https://www.googleapis.com/auth/admin.directory.group`
    - `https://www.googleapis.com/auth/admin.directory.group.member`
    - `https://www.googleapis.com/auth/admin.directory.domain.readonly`

### Select a user for the Delegated Subject

**Delegated Subject** is a required field when creating the Google Workspace provider in authentik. This field must be populated with the email address of a Google Workspace user with [suitable permissions](#delegated-subject-permissions).

1. In the sidebar navigate to **Directory** > **Users**.
2. Either select an existing user's email address or **Add new user** and define the user and email address to use as the Delegated Subject.
3. Take note of this email address as it will be required when creating the Google Workspace provider in authentik.

#### Delegated Subject permissions

:::warning
We do not recommend using an administrator account for the Delegated Subject user. A custom role should be used instead, see the [Google Admin console documentation](https://support.google.com/a/answer/2406043?hl=en) for more details.
:::

The Delagated Subject user requires the following permissions:

##### Admin console privilieges

- Users
- Groups

##### Admin API privileges

- Domain management
- Users
- Groups

Now that you have configured your Google Workspace organization, you are ready to [create a Google Workspace provider](./create-gws-provider.md).
