---
title: Enterprise features
description: "Features included in authentik Enterprise"
sidebar_position: 2
---

authentik Enterprise adds features for identity provisioning, security, compliance, and device access. These features are included with both Enterprise plans.

## Enterprise and Enterprise Plus

Enterprise includes all the product features on this page and ticket-based support for qualifying subscriptions.

Enterprise Plus includes everything in Enterprise, with additional options for organizations that need a customized agreement:

- Dedicated support channels (Slack and/or scheduled calls)
- Assistance with onboarding best practices
- SLA-backed response times
- Volume discounts for large teams
- Auditable FIPS-compliant deployments to meet FedRAMP requirements
- Billing and purchase via invoice

See the [pricing page](https://goauthentik.io/pricing/) for current plan details.

## Product features

### Identity and provisioning

- [Google Workspace integration](../add-secure-apps/providers/gws/index.md) synchronizes users and groups from authentik to Google Workspace.
- [Microsoft Entra ID integration](../add-secure-apps/providers/entra/index.md) synchronizes users and groups from authentik to Microsoft Entra ID.
- [External OAuth and SAML sources](../add-secure-apps/flows-stages/stages/source/index.md) embed an external identity provider in a flow for migration or additional verification.
- The [Shared Signals Framework provider](../add-secure-apps/providers/ssf/index.md) sends security events to subscribed applications, including Apple Business Manager.
- [OAuth authentication for SCIM](../add-secure-apps/providers/scim/index.md#oauth-token) uses short-lived OAuth tokens instead of a static token for SCIM provisioning.

### Authentication and network access

- [Password history compliance](../customize/policies/types/password-uniqueness.md) prevents users from reusing previous passwords.
- [Client certificate authentication](../add-secure-apps/flows-stages/stages/mtls/index.md) authenticates or enrolls users with client certificates from devices, smart cards, PIV cards, or hardware tokens. This feature is in preview.
- [RADIUS EAP-TLS](../add-secure-apps/providers/radius/index.mdx#eap) authenticates network clients with EAP-TLS and client certificates.

### Audit and reporting

- [Enhanced audit logging](../sys-mgmt/events/logging-events.mdx#enhanced-audit-logging) records detailed object changes and shows before-and-after values for compliance review.
- [CSV data exports](../sys-mgmt/data-exports.md) export user and event data for analysis, reporting, or backup.

### Device security

- The [Google Chrome connector](../endpoint-devices/device-compliance/connectors/google-chrome.md) uses Chrome Enterprise Device Trust signals in device-aware access decisions.
- [Local device login](../endpoint-devices/authentik-agent/device-authentication/local-device-login/index.mdx) enables users to sign in to Windows and Linux devices with authentik credentials. This feature is in preview.
- Advanced device compliance adds device facts and integrations to device-aware access decisions. This feature is in development; see the [Endpoint Devices feature overview](../endpoint-devices/index.mdx#features-overview).

Feature availability can change as preview features mature. Refer to the linked technical documentation for current platform support and configuration requirements.
