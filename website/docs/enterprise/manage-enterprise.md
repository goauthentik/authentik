---
title: Manage your Enterprise account
---

### Organization management

Your organization defines the members, their roles, the license associated with the organization, and account management for billing, payment methods, and invoice history.

#### **Create an Org**

note that to delete one, you need to open a ticket

#### Add/remove members of an organization\*\*

-   explain the roles
-   explain the forecast users

### License management

#### Buy a license

(explain the Install ID for those people who entered the Customer Portal without going through the Admin interface)

#### Difference between Internal and External users

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

-   How to view your license key

### Manage Billing
