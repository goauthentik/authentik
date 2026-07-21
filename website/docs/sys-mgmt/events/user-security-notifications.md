---
title: User security notifications
authentik_version: "2026.8"
---

authentik ships with a set of notification rules that email users about security-relevant changes to their own account. Unlike most [notification rules](./notifications.md), which are typically used to alert administrators, these rules send the email to the user affected by the event.

All of these rules are **disabled by default**.

## Default rules

| Notification rule                       | The user receives an email when...                                                                                                                                                                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `default-notify-user-password-change`   | Their password is changed in authentik ([`password_set`](./event-actions.md#password_set)). Password hashes cached from an external source login (for example, LDAP or Kerberos) and passwords set by blueprints do not trigger the notification.       |
| `default-notify-user-mfa-device-change` | An MFA device is added to or removed from their account ([`mfa_device_added` / `mfa_device_removed`](./event-actions.md#mfa_device_added--mfa_device_removed)).                                                                                         |
| `default-notify-user-impossible-travel` | A login to their account is blocked because of an impossible travel pattern — a [`login_blocked`](./event-actions.md#login_blocked) event with the `impossible_travel` reason, as created by a [GeoIP policy](../../customize/policies/types/geoip.md). |
| `default-notify-user-account-lockdown`  | Their account is locked down with [Account Lockdown](../../security/account-lockdown.md).                                                                                                                                                               |
| `default-notify-user-welcome`           | Their account is created via the Admin interface, the API, an enrollment flow, or a blueprint ([`user_created`](./event-actions.md#user_created)). Service accounts and accounts imported by a source sync do not receive the welcome email.            |

The first four rules deliver email through the `default-security-email-transport` notification transport, which renders the **Security Notification** email template; the welcome email uses `default-welcome-email-transport` with the **Account Welcome** template. The subject line of each email is derived from the event that triggered it.

## Enable a rule

authentik must be able to [send email](../../install-config/email.mdx) for these notifications to be delivered.

1. Log in as an administrator, open the authentik Admin interface, and navigate to **Events** > **Notification Rules**.
2. Click the **Edit** icon next to the rule that you want to enable.
3. Toggle **Enabled**, and then click **Update**.

## How it works

Each rule has [**Send notification to affected user**](./notifications.md#3-create-a-notification-rule-and-bind-it-to-the-policy) enabled, so the email is sent to the user recorded in the triggering event's `subject_uuid` context field — not to the user that caused the event. For example, when an administrator resets a user's password, the email goes to the user whose password was changed.

Events are matched by [Event Matcher policies](../../customize/policies/types/event-matcher.md) bound to each rule. The more specific conditions, such as excluding accounts imported by a source sync, are expressed as [AKQL](../akql.mdx#use-akql-in-an-event-matcher-policy) queries on the event context.

## Customize the default rules

The notification rules themselves are created once and are safe to edit: changes such as toggling **Enabled** or selecting a different transport or severity persist across upgrades.

The bound Event Matcher policies and the two notification transports are managed by a default [blueprint](../../customize/blueprints/index.mdx): whenever the blueprint is re-applied — after an authentik upgrade that changes it, or manually from the Admin interface — any manual changes to their configuration are overwritten. To customize the matching conditions or the emails, create your own policies or [transports](./transports.md) — for example, with a [custom email template](../../add-secure-apps/flows-stages/stages/email/index.md#custom-templates) — and use those on the rule instead of editing the managed objects.
