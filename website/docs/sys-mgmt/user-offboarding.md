---
title: User Offboarding
description: "Schedule automated deactivation or deletion of a user at a future time, with optional session and token revocation."
sidebar_label: User Offboarding
authentik_enterprise: true
authentik_version: "2026.8.0"
authentik_preview: true
---

User offboarding lets you schedule an automated action against a user — deactivating or deleting the account — to run at a specific future time. As part of the action, you can optionally revoke the user's active sessions and API tokens.

This is useful for planned departures: when an employee's last day is known in advance, you can schedule the offboarding ahead of time and let authentik carry it out at the right moment, without anyone needing to remember to act on the day.

You schedule an offboarding from a user's detail page, and you view and cancel scheduled offboardings from the **Events** > **Offboardings** page.

## Offboarding actions

An offboarding runs one of the following actions when its scheduled time is reached:

| Action         | Description                                                                                     |
| -------------- | ----------------------------------------------------------------------------------------------- |
| **Deactivate** | Marks the user as inactive so they can no longer log in. The account and its data are retained. |
| **Delete**     | Permanently removes the user account.                                                           |

Independently of the action, each offboarding has two revocation options:

| Option              | Description                                                          |
| ------------------- | -------------------------------------------------------------------- |
| **Revoke sessions** | Ends all of the user's active sessions, signing them out everywhere. |
| **Revoke tokens**   | Revokes all of the user's API tokens.                                |

Both options are enabled by default. Revoking sessions and tokens ensures the user loses access immediately when the offboarding runs, rather than remaining signed in until their existing sessions expire.

## Offboarding states

You can view every offboarding and its current state on the **Events** > **Offboardings** page. By default the page shows only pending offboardings; disable **Only show pending offboardings** to also see completed, failed, and canceled records.

| State         | Description                                                                   |
| ------------- | ----------------------------------------------------------------------------- |
| **Pending**   | The offboarding is scheduled and waiting for its execution time.              |
| **Completed** | The action ran successfully.                                                  |
| **Failed**    | The action could not be completed after the maximum number of retry attempts. |
| **Canceled**  | The offboarding was canceled before it ran.                                   |

## Schedule an offboarding

1. Navigate to **Directory** > **Users** and click the user you want to offboard.
2. On the user's detail page, in the user information card, click **Schedule Offboarding**.
3. Set the date and time to run the offboarding. It must be in the future.
4. Choose the **Action** (Deactivate or Delete), and enable or disable **Revoke sessions** and **Revoke tokens**.
5. Click **Schedule**.

The user's card now shows the scheduled time. A user can have only one pending offboarding at a time.

## How offboardings run

A background task periodically checks for pending offboardings whose scheduled time has passed and executes them. Because execution is time-based, the action runs shortly after the scheduled time rather than exactly at it.

If an execution fails — for example, because of a transient error — authentik automatically retries it. After the maximum number of attempts, the offboarding is marked **Failed** and is no longer retried.

When an offboarding completes, authentik writes a **User Offboarded** event to the [audit log](./events/index.md), attributed to the user who scheduled it and recording the action taken and which artifacts were revoked.

## Cancel an offboarding

While an offboarding is **Pending**, you can cancel it in either place:

- On the **Events** > **Offboardings** page, select the offboarding and click **Cancel**.
- On the user's detail page, click **Cancel offboarding** on the user information card.

Canceling does not remove the record. The offboarding is retained with a **Canceled** state so the audit trail — who scheduled it and who canceled it — remains intact. Only pending offboardings can be canceled.

## Restrictions

The following restrictions apply when scheduling or canceling offboardings:

- Each user can have only one pending offboarding at a time. Cancel the existing one before scheduling a new one.
- You cannot schedule an offboarding for your own account.
- You cannot cancel an offboarding that targets your own account. This is a separation-of-duties safeguard, so a user cannot rescue their own account from an offboarding scheduled by another administrator.
- Internal service accounts cannot be offboarded.
