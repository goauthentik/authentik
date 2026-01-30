---
title: Account Lockdown
authentik_version: "2026.2"
authentik_enterprise: true
---

Account Lockdown is a security feature that allows administrators to quickly secure a user account during emergencies, such as suspected compromise or unauthorized access. Users can also lock down their own account if they believe it has been compromised.

## What Account Lockdown does

When triggered, Account Lockdown performs the following actions (configurable per stage):

- **Deactivates the user account**: The user can no longer log in
- **Sets an unusable password**: Invalidates the user's password
- **Terminates all active sessions**: Immediately logs the user out of all devices and applications
- **Revokes all tokens**: Invalidates all API tokens and app passwords associated with the user account

An event is created that can be used to [trigger notifications via Notification Rules](#configure-notifications).

:::note Protected accounts
Account Lockdown cannot be triggered on:

- The anonymous user
- Internal service accounts
  :::

## How it works

Account Lockdown is implemented as a flow-based feature. When a lockdown is triggered:

1. The user is redirected to the configured **Lockdown Flow** (set on the Brand)
2. The flow displays a warning and collects a reason for the lockdown
3. The **Account Lockdown Stage** executes the lockdown actions
4. For admin-initiated lockdowns, a completion message shows the results
5. For self-service lockdowns, the user can be redirected to a separate **Completion Flow** (since their session is deleted)

## Configure the Lockdown Flow

A default lockdown flow is created when authentik is installed. To configure a custom flow:

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **System** > **Brands**.
3. Edit your brand and set the **Lockdown flow** to your desired flow.

The lockdown flow should contain:
- A **Prompt Stage** to display warnings and collect a reason
- An **Account Lockdown Stage** to perform the lockdown actions
- Optionally, a completion stage to show results (for admin lockdowns)

## Account Lockdown Stage settings

The Account Lockdown Stage can be configured with the following options:

| Setting | Description | Default |
|---------|-------------|---------|
| Deactivate user | Set the user's `is_active` to False | Enabled |
| Set unusable password | Invalidate the user's password | Enabled |
| Delete sessions | Terminate all active sessions | Enabled |
| Revoke tokens | Delete all API tokens and app passwords | Enabled |
| Completion flow | Flow to redirect users to after self-service lockdown (must not require authentication) | None |

## Trigger an Account Lockdown

### From the Users list

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Directory** > **Users**.
3. Select one or more users using the checkboxes.
4. Click the **Account Lockdown** button.
5. Review the warning and enter a reason for the lockdown (recorded in the event log).
6. Click **Continue** to execute the lockdown.

The completion screen will show success or failure status for each user.

### From a User's detail page

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Directory** > **Users**.
3. Click on a user to open their detail page.
4. Click the **Account Lockdown** button.
5. Review the warning and enter a reason for the lockdown.
6. Click **Continue** to execute the lockdown.

## Self-service Account Lockdown

Users can lock down their own account if they suspect it has been compromised. This is useful when a user notices suspicious activity and wants to immediately secure their account without waiting for an administrator.

### Lock your own account

1. Log in to authentik and open the User interface.
2. Navigate to **Settings**.
3. Scroll to the **Account Lockdown** section.
4. Click the **Lock my account** button.
5. You will be redirected to the lockdown flow.
6. Enter a reason describing why you are locking your account.
7. Click **Continue** to lock your account.

After locking your account, you will be redirected to a completion page with information about next steps. You will not be able to log back in until an administrator restores your access.

### Customize the self-service completion message

The message shown to users after they lock their own account is displayed in the **Completion Flow** configured on the Account Lockdown Stage. To customize this message:

1. Navigate to **Flows and Stages** > **Stages**.
2. Find the Account Lockdown Stage used in your lockdown flow.
3. Edit the stage and set the **Completion flow** to a flow that displays your custom message.

The completion flow should:
- Have **Authentication** set to **No authentication required** (the user's session is deleted)
- Contain a Prompt Stage with an alert field displaying your message

## Configure notifications

Account lockdown events can trigger notifications via the Notification Rules system using the **Account Lockdown Triggered** event type. This event is created for both administrator-triggered and self-service lockdowns.

To set up notifications:

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **Create** and select **Event Matcher Policy**.
4. Give the policy a name (e.g., "Match account lockdown events").
5. In the **Action** field, select **Account Lockdown Triggered**.
6. Click **Create** to save the policy.
7. Navigate to **Events** > **Notification Rules**.
8. Click **Create** to add a new notification rule.
9. Configure the rule:
    - **Name**: Give the rule a descriptive name
    - **Transports**: Select the notification transports (e.g., email, webhook)
    - **Severity**: Select the notification severity level
10. Click **Create** to save the notification rule.
11. In the notification rules list, click the arrow next to your new rule to expand it.
12. Click **Bind existing Policy/Group/User**.
13. Select the Event Matcher Policy you created and click **Create**.

## Restore access after lockdown

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Directory** > **Users**.
3. Find the locked user (they will show as inactive).
4. Click **Activate** to re-enable the account.
5. Use **Set password** or **Create Recovery Link** to set a new password.
6. Advise the user to review their account security settings and re-enroll any MFA devices.
