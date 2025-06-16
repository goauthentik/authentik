---
title: Endpoint Authenticator Google Device Trust Connector Stage
authentik_version: "2024.10"
authentik_preview: true
authentik_enterprise: true
---

With this stage, authentik can validate users' Chrome browsers and ensure that users' devices are compliant and up-to-date.

:::info
This stage only works with Google Chrome, as it relies on the [Chrome Verified Access API](https://developers.google.com/chrome/verified-access).
:::

## Configuration

The main steps to set up your Google workspace are as follows:

- [Configuration](#configuration)
    - [Create a Google cloud project](#create-a-google-cloud-project)
    - [Create a service account](#create-a-service-account)
    - [Set credentials for the service account](#set-credentials-for-the-service-account)
    - [Create the stage](#create-the-stage)

For detailed instructions, refer to Google documentation.

### Create a Google cloud project

1. Open the Google Cloud Console (https://cloud.google.com/cloud-console).
2. In upper left, click the drop-down box to open the **Select a project** box, and then select **New Project**.
3. Create a new project and give it a name like "authentik GWS".
4. Use the search bar at the top of your new project page to search for "API Library".
5. On the **API Library** page, use the search bar again to find "Chrome Verified Access API".
6. On the **Chrome Verified Access API** page, click **Enable**.

### Create a service account

1. After the new Chrome Verified Access API is enabled (it might take a few minutes), return to the Google Cloud console home page (click on **Google Cloud** in upper left).
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
   Later, when you create the stage in authentik, you will add this key in the **Credentials** field.
4. On the service account page, click the **Details** tab, and expand the **Advanced settings** area.
5. Log in to the Admin Console, and then navigate to **Chrome browser -> Connectors**.
6. Click on **New Provider Configuration**.
7. Under Okta, click "Set up".
8. Enter a name.
9. Enter the URL: https://authentik.company/endpoint/gdtc/chrome/
10. Under Service accounts, enter the full name of the service account created above, for example `authentik-gdtc-docs@authentik-enterprise-dev.iam.gserviceaccount.com`.

### Create the stage

1. Log in as an admin to authentik, and go to the Admin interface.

2. In the Admin interface, navigate to **Flows -> Stages**.

3. Click **Create**, and select **Endpoint Authenticator Google Device Trust Connector Stage**, and in the **New stage** box, define the following fields:

    - **Name**: define a descriptive name, such as "chrome-device-trust".

    - **Google Verified Access API**

        - **Credentials**: paste the contents of the JSON file (the key) that you downloaded earlier.

4. Click **Finish**.

After creating the stage, it can be used in any flow. Compared to other Authenticator stages, this stage does not require enrollment. Instead of adding an [Authenticator Validation Stage](../authenticator_validate/index.mdx), this stage only verifies the users' browser.
