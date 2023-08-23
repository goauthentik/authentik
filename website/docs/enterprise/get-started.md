---
title: Get started
---

Installing authentik is exactly the same process for both Enterprise version and our free OSS version. Refer to our [technical documentation](../installation/index.md) for instructions to install and configure authentik.

> This preview version of Enterprise authentik is available within our 2023.8.x release and later.

## Install Enterprise

To get started working with the preview edition of Enterprise authentik, upgrade to the 2023.8.x version. For installation steps, [technical documentation](../installation/index.md) for instructions to install and configure authentik.

-   [Docker Compose installation](../installation/docker-compose.md)
-   [Kubernetes instalation](../installation/kubernetes.md)

## Access Enterprise

After you have installed authentik, you can access your Enterprise features by first getting a license for the organization.

The license key provides access to the Customer Portal, where you define your organization and its members, manage billing, and access our Support center to open tickets and view current requests.

1. To get a license key, log in to your authentik account as usual, and click on **Admin interface** in the upper right.

!["Admin interface licenses page"](./licenses-page-admin.png)

2. On the **Admin interface**, navigate to **Enterprise → Licenses** in the left menu, and then click **Go to customer portal** under the **Get a license** section.

3. In the Authentik login screen, sign up and then log in to the Customer Portal.

4. In the Customer Portal, if you have not already created an Organization (nor been invited to join one), you are first be prompted to create an organization.

    For details about creating an organization, refer to [Manage your Enterprise account](./manage-enterprise.md#organization-management).

5. In the Customer Portal, on the **Purchase a license** page, review the pricing plans and, optionally, change the name of the license. (The name is simply a nickname, a convenient way to label the license.)

6. Click **Continue** to display the checkout page. Select the number of users, provide your payment information, and then click **Subscribe**.

NOTES for me: after they click Subscribe, payment verification happens...

redirected to the Customer portal Organization page... which dipslays success or not... in the background, the license is created. The user will see a message during the verification stage, saying "your license will be created now."

NOTE: user will have to refresh the page to get the license... figure out how to word this to not sound too bad. It only takes seconds...

When ready, the license shows on the Org page in the list, for that org.

7. To retrieve your license key, click on Details beside the license and .... copy the key.

8. Go back to the Admin interface, navigate to **Enterprise -> Licenses** page, click on **Install** and paste the key, and then click **Install**.

To verify that it all works, the expriry date will show one year. (Ask Jens to add green mark of success.)

> For information about managing your Enterprise organizations, billing, and licenses, refer to [Manage your Enterprise account](./manage-enterprise.md)].
