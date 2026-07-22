---
title: User security notifications
description: "Email notifications for users about security-related account changes"
authentik_version: "2026.8"
---

authentik provides notification rules that inform users when security-relevant changes are made to their accounts. Unlike most [notification rules](./notifications.md), which typically notify administrators, these rules send email notifications directly to the user affected by the event.

User security notification rules are **disabled by default**.

## Overview

| Notification rule                       | The user receives an email when...                                                                                                                                                                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `default-notify-user-password-change`   | Their password is changed in authentik ([`password_set`](./event-actions.md#password_set)). Password hashes cached from an external source login (for example, LDAP or Kerberos) and passwords set by blueprints do not trigger the notification.       |
| `default-notify-user-mfa-device-change` | An MFA device is added to or removed from their account ([`mfa_device_added` / `mfa_device_removed`](./event-actions.md#mfa_device_added--mfa_device_removed)).                                                                                         |
| `default-notify-user-impossible-travel` | A login to their account is blocked because of an impossible travel pattern — a [`login_blocked`](./event-actions.md#login_blocked) event with the `impossible_travel` reason, as created by a [GeoIP policy](../../customize/policies/types/geoip.md). |
| `default-notify-user-account-lockdown`  | Their account is locked down with [Account Lockdown](../../security/account-lockdown.md).                                                                                                                                                               |
| `default-notify-user-welcome`           | Their account is created via the Admin interface, the API, an enrollment flow, or a blueprint ([`user_created`](./event-actions.md#user_created)). Service accounts and accounts imported by a source sync do not receive the welcome email.            |

The first four notification rules deliver email through the `default-security-email-transport` notification transport, which renders the **Security Notification** email template; the welcome notification rule uses `default-welcome-email-transport` with the **Account Welcome** template. The subject line of each email is derived from the event that triggered it.

## Enable a notification rule

To deliver these notifications, authentik must first be configured to [send email](../../install-config/email.mdx).

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Events** > **Notification Rules**.
3. Select the **Edit** icon next to the rule you want to enable.
4. Enable the **Enabled** toggle, then click **Update** to save your changes.

## How it works

Each notification rule has [**Send notification to affected user**](./notifications.md#3-create-a-notification-rule-and-bind-it-to-the-policy) enabled, so the email is sent to the user recorded in the triggering event's `subject` context field — not to the user that caused the event. For example, when an administrator resets a user's password, the email goes to the user whose password was changed.

Events are matched by [Event Matcher policies](../../customize/policies/types/event-matcher.md) bound to each rule. The more specific conditions, such as excluding accounts imported by a source sync, are expressed as [AKQL](../akql.mdx#use-akql-in-an-event-matcher-policy) queries on the event context.

## Customize the notification rules

The notification rules can be safely modified. Any changes to a notification rule’s configuration, such as its **Enabled** state, notification transport, or severity level, are preserved during upgrades.

The bound Event Matcher policies and the two notification transports are managed by a default [blueprint](../../customize/blueprints/index.mdx). When this blueprint is reapplied, either during an authentik upgrade that updates it or manually from the Admin interface, any manual changes to these blueprint-managed objects are overwritten.

To customize event-matching conditions or notification emails, create your own [policies](../../customize/policies/types/event-matcher.md) or [notification transports](./transports.md). For example, you can create a transport that uses a [custom email template](../../add-secure-apps/flows-stages/stages/email/index.md#custom-templates), then select this transport on the notification rule rather than modifying blueprint-managed notification transport.
