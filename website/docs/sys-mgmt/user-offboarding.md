---
title: User offboarding
description: "Schedule the deactivation or deletion of a user, with optional session and token revocation."
sidebar_label: User offboarding
authentik_enterprise: true
authentik_version: "2026.8.0"
authentik_preview: true
---

User offboarding lets you schedule the deactivation or deletion of a user account for a future date and time. You can also revoke the user's sessions and tokens when the offboarding runs.

For example, you can schedule an offboarding as soon as you know an employee's last day instead of relying on an administrator to update the account that day.

## Choose an offboarding action

Each offboarding performs one of the following actions:

- **Deactivate**: Marks the user as inactive so that they can no longer log in. The user account and its data remain in authentik.
- **Delete**: Permanently deletes the user account.

You can apply either action with the following options:

- **Revoke sessions**: Ends the user's active sessions.
- **Revoke tokens**: Revokes the user's tokens and related credentials.

Both options are enabled by default. Leave them enabled to prevent existing sessions or credentials from retaining access after the offboarding runs.

## Schedule a user offboarding

You cannot schedule an offboarding for your own account or for an internal service account. Each user can have only one pending offboarding.

1. In the Admin interface, go to **Directory** > **Users**.
2. Select the user, and then click **Schedule Offboarding** in the **Actions** section.
3. Select **Deactivate** or **Delete** for the **Action**.
4. In **Scheduled for**, enter a future date and time.
5. Configure **Revoke sessions** and **Revoke tokens**.
6. Click **Schedule**.

The **Schedule Offboarding** button changes to **Cancel Offboarding**. You can also find the scheduled offboarding under **Events** > **Offboardings**.

## Monitor user offboardings

The **Events** > **Offboardings** page shows pending offboardings by default. Disable **Only show pending offboardings** to include available completed, failed, and canceled records.

| State         | Description                                                                                         |
| ------------- | --------------------------------------------------------------------------------------------------- |
| **Pending**   | The offboarding is waiting for its scheduled date and time.                                         |
| **Completed** | The offboarding completed successfully.                                                             |
| **Failed**    | The offboarding did not complete after five attempts. Changes from failed attempts are rolled back. |
| **Canceled**  | An administrator canceled the offboarding before it ran. The canceled record remains in the list.   |

authentik checks for due offboardings every five minutes. The action normally starts within five minutes after the scheduled time, but a task backlog can delay it further. If an attempt fails, authentik retries the complete offboarding action. After five failed attempts, the offboarding is marked **Failed** and is not retried again.

After an offboarding completes, authentik writes a **User Offboarded** event to the [audit log](./events/index.md). The event identifies the administrator who scheduled the offboarding, the selected action, and whether session and token revocation were enabled.

:::note
A successful **Delete** action removes the offboarding record with the user account. The **User Offboarded** event remains in the audit log.
:::

## Cancel a user offboarding

You can cancel only a pending offboarding. Use either of the following methods:

- On the user's details page, click **Cancel Offboarding**, review the scheduled action, and confirm the cancellation.
- On the **Events** > **Offboardings** page, select the offboarding, click **Cancel**, and confirm the cancellation.

Canceling changes the offboarding to **Canceled** and allows you to schedule another offboarding for the user. You cannot cancel an offboarding that targets your own account.
