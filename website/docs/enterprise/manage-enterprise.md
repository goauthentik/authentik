---
title: Manage your Enterprise account
---

## Organization management

Your organization defines the members, their roles, the license associated with the organization, and account management for billing, payment methods, and invoice history.

### **Create an Organization**

1. To create a new organization, log in to the Customer portal.

2. On the **My organizations** page, click **Create an organization**.

3. Specify the organization's name and notification email address, and then click **Create**.

    Your new organization page displays.

:::info
If you need to delete an organization open a ticket in the Support center.
:::

### Add/remove members of an organization

In the customer portal you can remove members and invite new members to the organization. When you invite new members, you can specify the role for the new member.

-   **Membe**r: can view licenses, including the license key.
-   **Owner**: can do everything the Member role can do, plus adding and removing members. Can order and renew licenses. Can edit the organization.

1. To manage membership in an organization, log in to the Customer portal.

2. On the **My organizations** page, click the name of the organization you want to edit membership in.

    Your organization page displays.

    - To remove a member, scroll down to the **Membership** area and then click **Remove** beside the name of the member.

    - To invite a new member, scroll down to the **Pending invitations** area, and enter the email address for the person, select the role, and then click **Invite**.

    A message appears that the invitation has been sent. When the recipient accepts the invitation by clicking a link in the email, they will be added to the organization.

    TO BE WRITTEN
    vvvvvvvvvvvv

-   explain the forecast users

### License management

### Buy a license

(explain the Install ID for those people who entered the Customer Portal without going through the Admin interface)

### Difference between Internal and External users

-   How the license usage is calculated (for default and external users)

    -   authentik regularly captures the user counts and records them. This data is checked against all valid licenses, whose user count is summed. The default user count is calculated as-is and the external users are calculated based on how many external users were active since start of the current month.

-   How the expiry works

    -   Expiry works by summarizing all valid licenses together and picking the lowest expiry date. However after the license expiring earliest expires, all calculations will be updated without that license.

-   How the license violation works

    -   After 2 weeks of overage admins get a warning banner

    -   After another 2 weeks, users get a warning banner

    -   After another 2 weeks, the authentik goes “read-only”

    Basically in the admin interface only the license can be updated

    But the rest of the functionality is still there as is

### How to view your license key

### Manage Billing
