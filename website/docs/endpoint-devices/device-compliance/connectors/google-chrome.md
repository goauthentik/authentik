---
title: Google Chrome connector
tags: [device compliance, compliance, connectors, google, chrome, device, trust]
authentik_version: "2026.5"
authentik_enterprise: true
---

With this connector, authentik can validate users' Chrome browsers and ensure that users' devices are compliant and up-to-date.

Support for the Chrome Enterprise Device Trust connector allows organizations to integrate Chrome browsers and ChromeOS devices with authentik as the Identity Provider (IdP), to strengthen their overall security posture.

Device Trust is particularly important in environments with many different device types that are used by a large, remote workforce that might have a BYOD (Bring Your Own Device) policy, or have large teams of contractors, temporary workers, or volunteers.

With Device Trust you can enable "context-aware" access policies; for example a policy might require that a device have all security patches installed.

:::info
This connector only works with Google Chrome, as it relies on the [Chrome Verified Access API](https://developers.google.com/chrome/verified-access).
:::

## Configuration

The main steps to set up your Google workspace are as follows:

- [Create a Google cloud project](#create-a-google-cloud-project)
- [Create a service account](#create-a-service-account)
- [Set credentials for the service account](#set-credentials-for-the-service-account)
- [Create the connector](#create-the-connector)

For detailed instructions, refer to Google documentation.

### Create a Google cloud project

1. Log in to the [Google Cloud Console](https://cloud.google.com/cloud-console) as an administrator.
2. In the upper left, click the drop-down box to open the **Select a project** box, and then select **New Project**.
3. Create a new project and give it a name like "authentik Chrome Device Trust".
4. Use the search bar at the top of your new project page to search for "API Library".
5. On the **API Library** page, use the search bar again to find "Chrome Verified Access API".
6. On the **Chrome Verified Access API** page, click **Enable**.

### Create a service account

1. After the new Chrome Verified Access API is enabled (it might take a few minutes), return to the Google Cloud console home page (click on **Google Cloud** in the upper left).
2. Use the search bar to find and navigate to the **IAM** page.
3. On the **IAM** page, click **Service Accounts** in the left navigation pane.
4. At the top of the **Service Accounts** page, click **Create Service Account**.

- Under **Service account details** page, define the **Name** and **Description** for the new service account, and then click **Create and Continue**.
- Under **Grant this service account access to project** you do not need to define a role, so click **Continue**.
- Under **Grant users access to project** you do not need to define a role, so click **Done** to complete the creation of the service account.

### Set credentials for the service account

1. On the **Service accounts** page, click the account that you just created.
2. Click the **Keys** tab at top of the page, then click **Add Key** > **Create new key**.
3. In the Create box, select JSON as the key type, and then click **Create**.
   A pop-up displays with the private key, and the key is saved to your computer as a JSON file.
   Later, when you create the connector in authentik, you will add this key in the **Credentials** field.
4. On the service account page, click the **Details** tab, and expand the **Advanced settings** area.
5. Log in to the Admin Console, and then navigate to **Chrome browser** > **Connectors**.
6. Click on **New Provider Configuration**.
7. Under **Universal Device Trust**, click **Set up**.
8. Provide a name and set the URL to `https://authentik.company/endpoint/gdtc/chrome/`.
9. Under **Service accounts**, enter the full name of the service account created above, for example `authentik-gdtc@authentik-enterprise-dev.iam.gserviceaccount.com`.

### Create the connector

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors** and click **New Endpoint Connector**.
3. Select **Google Device Trust Connector** as the connector type, click **Next**, and configure the following settings:
    - **Name**: define a descriptive name, such as "chrome-device-trust".
    - **Google Verified Access API**
        - **Credentials**: paste the contents of the JSON file (the key) that you downloaded earlier.

4. Click **Finish**.

After creating the connector, it can be used in the [Endpoint Stage](../../../add-secure-apps/flows-stages/stages/endpoint/index.md). Refer to [Device compliance policy](../device-compliance-policy.md) for more information on using device facts from the connector in a flow.
