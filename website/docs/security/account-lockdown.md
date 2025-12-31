---
title: Account Lockdown
authentik_version: "2026.2"
---

Account Lockdown is a security feature that allows administrators to quickly secure a user account in emergency situations, such as suspected compromise or unauthorized access.

:::info Enable or disable account lockdown
Account Lockdown can be enabled or disabled in **System** > **Settings** under **Enable account lockdown**.
:::

:::info Security email address
The security email address for notifications can be configured in **System** > **Settings** under **Security email**.
:::

## What Account Lockdown does

When triggered, Account Lockdown performs the following actions:

- **Deactivates the user account**: The user can no longer log in
- **Resets the user's password**: Sets a new random password, invalidating the old one
- **Terminates all active sessions**: Immediately logs the user out of all devices and applications
- **Revokes all tokens**: Invalidates all API tokens, OAuth access tokens, and refresh tokens

An event is created that can be used to [trigger notifications via Notification Rules](#configure-notifications).

:::note Protected accounts
Account Lockdown cannot be triggered on:

- Your own account
- The anonymous user
- Internal service accounts
  :::

## Trigger an Account Lockdown for a single user

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users**.
3. Click on the user you want to lock down.
4. Click the **Account Lockdown** button.
5. Enter a reason for the lockdown (this is logged for audit purposes).
6. Click **Trigger Lockdown**.

## Trigger an Account Lockdown for multiple users

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users**.
3. Select the users you want to lock down using the checkboxes.
4. Click the **Account Lockdown** button in the toolbar.
5. Enter a reason for the lockdown.
6. Click **Trigger Lockdown**.

## Configure notifications

Account lockdown events can trigger notifications via the Notification Rules system. To set up notifications:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create** and select **Event Matcher Policy**.
4. Give the policy a name (e.g., "Match account lockdown events").
5. In the **Action** field, select **Account Lockdown Triggered**.
6. Click **Create** to save the policy.
7. Navigate to **Events** > **Notification Rules**.
8. Click **Create** to add a new notification rule.
9. Configure the rule:
    - **Name**: Give the rule a descriptive name
    - **Send email to security address**: Enable to send notifications to the security email configured in **System** > **Settings**
    - **Transports**: Select the notification transports (e.g., email, webhook)
    - **Severity**: Select the notification severity level
10. Click **Create** to save the notification rule.
11. In the notification rules list, click the arrow next to your new rule to expand it.
12. Click **Bind existing Policy/Group/User**.
13. Select the Event Matcher Policy you created and click **Create**.

## Restore access after lockdown

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users**.
3. Find the locked user.
4. Click **Activate** to re-enable the account.
5. Use **Set password** or **Create Recovery Link** to set a new password.
6. Advise the user to review their account security settings.
