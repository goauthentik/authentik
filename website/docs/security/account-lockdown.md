---
title: Account Lockdown
authentik_version: "2026.2"
authentik_enterprise: true
---

Account Lockdown is a security feature that allows administrators to quickly secure a user account during emergencies, such as suspected compromise or unauthorized access. Users can also lock down their own account if they believe it has been compromised.

## What Account Lockdown does

When triggered, Account Lockdown performs the following actions (all configurable):

- **Deactivates the user account**: The user can no longer log in
- **Sets an unusable password**: Invalidates the user's password
- **Terminates all active sessions**: Immediately logs the user out of all devices and applications
- **Revokes all tokens**: Invalidates API, app password, recovery, and verification tokens
- **Creates an audit event**: Records the lockdown with the provided reason (can trigger [notifications](#configure-notifications))

:::note Protected accounts
Account Lockdown cannot be triggered on the anonymous user or internal service accounts.
:::

## Prerequisites

1. A **Lockdown Flow** must be configured on your Brand (**System** > **Brands**)
2. The flow must contain an [Account Lockdown Stage](../add-secure-apps/flows-stages/stages/account_lockdown/index.md) (Enterprise)
3. For self-service lockdown, configure a **Completion Flow** on the stage or customize the self-service message

## The default lockdown flow

authentik includes a default lockdown flow (`default-account-lockdown`) with:

| Order | Stage                     | Purpose                          |
| ----- | ------------------------- | -------------------------------- |
| 0     | Prompt Stage              | Warning message and reason input |
| 10    | Account Lockdown Stage    | Executes lockdown actions        |
| 20    | Prompt Stage (admin only) | Shows results                    |

A separate completion flow (`default-account-lockdown-complete`) displays a message after self-service lockdowns.

### Use the default flow

1. Navigate to **System** > **Brands**.
2. Edit your brand and set **Lockdown flow** to `default-account-lockdown`.

### Create a custom flow

1. Navigate to **Flows and Stages** > **Flows** and create a flow with:
    - **Designation**: Stage Configuration
    - **Authentication**: Require authenticated user
2. Add a Prompt Stage for warnings and reason collection
3. Add an Account Lockdown Stage
4. Optionally add a results Prompt Stage (with policy to hide for self-service)
5. Set this flow as **Lockdown flow** on your Brand

For stage configuration details, see the [Account Lockdown Stage documentation](../add-secure-apps/flows-stages/stages/account_lockdown/index.md).

## Trigger an Account Lockdown

### From the Users list

1. Navigate to **Directory** > **Users**.
2. Select one or more users using the checkboxes.
3. Click **Account Lockdown**.
4. Review the warning, enter a reason (recorded in the audit log), and click **Continue**.
5. The results screen shows success or failure for each user.

:::note
If the bulk selection includes your own account and the stage deletes sessions, your current session is terminated as part of lockdown. In that case, authentik redirects to the self-service completion flow/message and the admin results stage is skipped.
:::

### From a User's detail page

1. Navigate to **Directory** > **Users** and click on a user.
2. Click **Account Lockdown**.
3. Review the warning, enter a reason (recorded in the audit log), and click **Continue**.
4. The results screen shows the lockdown status.

## Self-service Account Lockdown

Users can lock their own account from the User interface:

1. Navigate to **Settings**.
2. In the **Account Lockdown** section, click **Lock my account**.
3. Enter a reason and click **Continue**.

After lockdown, the user can be redirected to a completion page (if configured) or see the stage's self-service message. They cannot log back in until an administrator restores access.

### Configure the completion message

Since the user's session is deleted, the stage can either show a built-in message or redirect to a separate unauthenticated flow:

1. Create a flow with **Authentication** set to **No authentication required**
2. Add a Prompt Stage with an alert field containing your message
3. On your Account Lockdown Stage, set **Completion flow** to this flow (optional if using the stage message)

## Configure notifications

Use Notification Rules to alert when lockdowns occur:

1. Navigate to **Customization** > **Policies** and create an **Event Matcher Policy**
2. Set **Action** to **Account Lockdown Triggered**
3. Navigate to **Events** > **Notification Rules** and create a rule
4. Bind the Event Matcher Policy to the rule

## Restore access after lockdown

1. Navigate to **Directory** > **Users** and find the locked user (shown as inactive).
2. Click **Activate** to re-enable the account.
3. Use **Set password** or **Create Recovery Link** to set a new password.
4. Advise the user to re-enroll MFA devices.

## Troubleshooting

| Issue                         | Solution                                                                                  |
| ----------------------------- | ----------------------------------------------------------------------------------------- |
| "No lockdown flow configured" | Set a lockdown flow on your Brand (**System** > **Brands**)                               |
| Self-service shows login page | Configure a **Completion flow** on the stage with **No authentication required**          |
| Warning message not showing   | Ensure **Initial value expression** is enabled and field type is an alert type            |
| Bulk lockdown not working     | Ensure expressions handle `lockdown_target_users` (list), not just `lockdown_target_user` |
| Bulk including self skips results | Expected when **Delete sessions** is enabled; your session is terminated and self-service completion is shown |
