---
title: Get started
---

Installing authentik is exactly the same process for both Enterprise version and our free open source version.

> This preview version of Enterprise authentik is available within our 2023.8.x release and later.

## Install Enterprise

To get started working with the preview edition of Enterprise authentik, upgrade to the [2023.8.x version](../releases). For installation steps, [technical documentation](../installation/index.md) for instructions to install and configure authentik.

-   [Docker Compose installation](../installation/docker-compose.md)
-   [Kubernetes installation](../installation/kubernetes.md)

## Access Enterprise

Access your Enterprise features by first getting a license for the organization.

The license key provides access to the Customer portal, where you define your organization and its members, manage billing, and access our Support center to open tickets and view current requests.

1. To get a license key, log in to your authentik account with your admin credentials, and then click **Admin interface** in the upper right.

!["Admin interface licenses page"](./licenses-page-admin.png)

2. On the **Admin interface**, navigate to **Enterprise → Licenses** in the left menu, and then click **Go to Customer portal** under the **Get a license** section.

3. In the Authentik login screen, sign up and then log in to the Customer Portal.

    In the Customer Portal, if you have not already created an Organization (nor been invited to join one), you are first prompted to create an organization.

4. On the **My organizations** page, click **Create an organization**.

5. Specify the organization's name and notification email address, and then click **Create**.

    For more information about organizations, refer to [Manage your Enterprise account](./manage-enterprise.md#organization-management).

    Your new organization page displays.

6. Click **Purchase license**, and then on the **Purchase a license** page, review the pricing plans and (optionally) change the name of the license. The name is simply a nickname, a convenient way to label the license.

7. Click **Continue** to display the checkout page. Select the number of users, provide your payment information, and then click **Subscribe**.

When payment verification is complete, you are redirected to the **My organizations** page, where you should see a message saying "Successful purchase. Your license will appear here once we've validated your payment. If it doesn't, please contact us."

    When ready, the license displays on the organization's page.

7. To retrieve your license key, click on **Details** beside the license name and copy the key to your clipboard.

8. Go back to the Admin interface, navigate to **Enterprise -> Licenses** page, click on **Install**, paste the key, and then click **Install**.

## License verification

To verify that the license was successfully installed, confirm that the expriry date on the **Enterprise --> Licenses** page displays a date one year later.

> For information about managing your Enterprise organizations, billing, and licenses, refer to [Manage your Enterprise account](./manage-enterprise.md)].
