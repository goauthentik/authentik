---
title: Account Lockdown
authentik_version: "2025.5.0"
authentik_enterprise: true
---

Account Lockdown is a security feature that allows administrators to quickly secure a user account during emergencies, such as suspected compromise or unauthorized access. Users can also lock down their own account if they believe it has been compromised.

## What Account Lockdown does

When triggered, Account Lockdown performs the following actions (all configurable):

- **Deactivates the user account**: The user can no longer log in
- **Sets an unusable password**: Invalidates the user's password
- **Terminates all active sessions**: Immediately logs the user out of all devices and applications
- **Revokes all tokens**: Invalidates API, app password, recovery, verification, and OAuth2 tokens and grants
- **Creates an audit event**: Records the lockdown with the provided reason (can trigger [notifications](#configure-notifications))

:::note Protected accounts
Account Lockdown cannot be triggered on the anonymous user or internal service accounts.
:::

## Prerequisites

1. A **Lockdown Flow** must be configured on your Brand (**System** > **Brands**)
2. The flow must contain an [Account Lockdown Stage](../add-secure-apps/flows-stages/stages/account_lockdown/index.md) (Enterprise)
3. For self-service lockdown, configure a **Completion Flow** on the stage

## Use the packaged lockdown blueprint

authentik includes a packaged lockdown blueprint that creates a default lockdown flow (`default-account-lockdown`) and a self-service completion flow (`default-account-lockdown-complete`).

The blueprint creates:

| Order | Stage                     | Purpose                          |
| ----- | ------------------------- | -------------------------------- |
| 0     | Prompt Stage              | Warning message and reason input |
| 10    | Account Lockdown Stage    | Executes lockdown actions        |
| 20    | Prompt Stage (admin only) | Shows a confirmation message     |

A separate completion flow (`default-account-lockdown-complete`) displays a message after self-service lockdowns.

### Step 1. Download the blueprint

Download the lockdown blueprint by running:

```shell
wget https://goauthentik.io/blueprints/example/flow-default-account-lockdown.yaml
```

Alternatively, use this <DownloadLink to="/blueprints/example/flow-default-account-lockdown.yaml">link</DownloadLink> to view and save the file.

### Step 2. Import the blueprint file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows** and click **Import**.
3. Click **Choose file**, select `flow-default-account-lockdown.yaml`, and then click **Import**.

### Step 3. Set the lockdown flow on your brand

1. Navigate to **System** > **Brands**.
2. Edit your brand and set **Lockdown flow** to `default-account-lockdown`.

## Create a custom flow

1. Navigate to **Flows and Stages** > **Flows** and create a flow with:
    - **Designation**: Stage Configuration
    - **Authentication**: Require authenticated user
2. Add a Prompt Stage for warnings and reason collection
3. Add an Account Lockdown Stage
4. Optionally add an administrator-only completion Prompt Stage
5. Set this flow as **Lockdown flow** on your Brand

For stage configuration details, see the [Account Lockdown Stage documentation](../add-secure-apps/flows-stages/stages/account_lockdown/index.md).

## Trigger an Account Lockdown

### From a User's detail page

1. Navigate to **Directory** > **Users** and click on a user.
2. Click **Account Lockdown**.
3. Review the warning, enter a reason (recorded in the audit log), and click **Continue**.
4. If your flow includes an administrator-only completion stage, it is shown after the lockdown completes.

## Self-service Account Lockdown

Users can lock their own account from the User interface:

1. Navigate to **Settings**.
2. In the **Account Lockdown** section, click **Lock my account**.
3. Enter a reason and click **Continue**.

After lockdown, the user is redirected to the configured completion page. They cannot log back in until an administrator restores access.

### Configure the completion message

Since the user's session is deleted, the stage redirects to a separate unauthenticated flow:

1. Create a flow with **Authentication** set to **No authentication required**
2. Add a Prompt Stage with an alert field containing your message
3. On your Account Lockdown Stage, set **Completion flow** to this flow

## Configure notifications

Use Notification Rules to alert when lockdowns occur:

1. Navigate to **Customization** > **Policies** and create an **Event Matcher Policy**
2. Set **Action** to **User Write**
3. Set **Query** to `action = "user_write" and context.action_id = "account_lockdown"`
4. Navigate to **Events** > **Notification Rules** and create a rule
5. Select a notification transport, such as `default-email-transport`
6. Select a destination group, or enable **Send notification to event user** to notify the locked user
7. Bind the Event Matcher Policy to the rule

## Restore access after lockdown

1. Navigate to **Directory** > **Users** and find the locked user (shown as inactive).
2. Click **Activate** to re-enable the account.
3. Use **Set password** or **Create Recovery Link** to set a new password.
4. Advise the user to re-enroll MFA devices.

## Troubleshooting

| Issue                         | Solution                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------- |
| "No lockdown flow configured" | Set a lockdown flow on your Brand (**System** > **Brands**)                      |
| Self-service shows login page | Configure a **Completion flow** on the stage with **No authentication required** |
| Warning message not showing   | Ensure **Initial value expression** is enabled and field type is an alert type   |
