---
title: Enterprise features
description: "Features included in authentik Enterprise"
---

This page describes the Enterprise features that are available in the authentik [Enterprise plans](https://goauthentik.io/pricing/).

## Enterprise vs Enterprise Plus

The Enterprise release of authentik is available in two tiers: Enterprise and Enterprise Plus.

Enterprise builds on authentik's open-source foundation with additional enterprise-focused features and integrations as well as ticket-based support.

Enterprise Plus includes everything in Enterprise, plus dedicated support channels (Slack and/or scheduled calls), assistance with onboarding best practices, SLA-backed response times, volume discounts for large teams, and auditable FIPS-compliant deployments to meet FedRAMP requirements. It also supports billing and purchase via invoice.

Both Enterprise and Enterprise Plus plans include all the following features:

## Features

### Enhanced logging

<<<<<<< HEAD
#### [Enhanced audit logging for compliance](../sys-mgmt/events/logging-events.mdx#enhanced-audit-logging)
=======
- [Google Workspace integration](../add-secure-apps/providers/gws/index.md) synchronizes users and groups from authentik to Google Workspace.
- [Microsoft Entra ID integration](../add-secure-apps/providers/entra/index.md) synchronizes users and groups from authentik to Microsoft Entra ID.
- [External OAuth and SAML sources](../add-secure-apps/flows-stages/stages/source/index.md) embed an external identity provider in a flow for migration or additional verification. For example, dynamically redirect users to authenticate against Entra ID or GWS before continuing with a flow.
- The [Shared Signals Framework provider](../add-secure-apps/providers/ssf/index.md) sends security events to subscribed applications, including Apple Business Manager.
- [OAuth authentication for SCIM](../add-secure-apps/providers/scim/index.md#oauth-token) uses short-lived OAuth tokens instead of a static token for SCIM provisioning.
- The [WS-Federation provider](../add-secure-apps/providers/wsfed/index.md) connects applications that use WS-Federation to authentik for single sign-on.
>>>>>>> 76c711371 (website/docs: remove preview tag from mtls stage doc (#23951))

Enhanced audit logging captures detailed model changes with "before" and "after" states, including many-to-many relationships, for comprehensive compliance tracking.

<<<<<<< HEAD
#### [Viewing logs in maps and charts](../sys-mgmt/events/logging-events.mdx#viewing-events-in-maps-and-charts)
=======
- [Password history compliance](../customize/policies/types/password-uniqueness.md) prevents users from reusing previous passwords.
- [Client certificate authentication](../add-secure-apps/flows-stages/stages/mtls/index.md) authenticates or enrolls users with client certificates from devices, smart cards, PIV cards, or hardware tokens.
- [RADIUS EAP-TLS](../add-secure-apps/providers/radius/index.mdx#eap) authenticates network clients with EAP-TLS and client certificates.
- [Account Lockdown](../security/account-lockdown.md) immediately secures a compromised account by disabling it, revoking its tokens, ending its sessions, and recording the action in the audit log.
>>>>>>> 76c711371 (website/docs: remove preview tag from mtls stage doc (#23951))

View recent events on both a world map view with pinpoints indicating where each event occurred and also a color-coded chart that highlights event types and volume.

<<<<<<< HEAD
#### [Exporting logs](../sys-mgmt/events/logging-events.mdx#export-events)
=======
- [Enhanced audit logging](../sys-mgmt/events/logging-events.mdx#enhanced-audit-logging) records detailed object changes and shows before-and-after values for compliance review.
- [Event maps and charts](../sys-mgmt/events/logging-events.mdx#viewing-events-in-maps-and-charts) visualize recent events by location, type, and volume.
- [CSV data exports](../sys-mgmt/data-exports.md) export user and event data for analysis, reporting, or backup.
- [Object Lifecycle Management](../sys-mgmt/object-lifecycle-management.md) schedules periodic reviews of applications, groups, and roles, assigns reviewers, and tracks overdue reviews. This feature is in preview.
>>>>>>> 76c711371 (website/docs: remove preview tag from mtls stage doc (#23951))

You can export authentik event logs to a CSV file.

### [Google Workspace integration](../add-secure-apps/providers/gws/index.md)

The Google Workspace provider syncs users and groups from authentik to Google Workspace, making authentik the source of truth. It supports direct syncs for real-time changes and automatically linking existing entities.

### [Microsoft Entra ID integration](../add-secure-apps/providers/entra/index.md)

The Microsoft Entra ID provider synchronizes users and groups from authentik to Microsoft Entra ID, making authentik the source of truth. It supports direct syncs for real-time changes and automatically linking existing entities.

### [Embed external OAuth/SAML sources](../add-secure-apps/flows-stages/stages/source/index.md)

The Source Stage embeds external OAuth or SAML providers into authentik flows for dynamic user verification. It enables integration with legacy IdPs (e.g., Okta) during migrations.

### [Chrome Enterprise Device Trust connector](../add-secure-apps/flows-stages/stages/authenticator_endpoint_gdtc/index.md)

This authenticator stage validates Chrome browsers and ChromeOS devices against enterprise policies, ensuring compliance before access. It integrates authentik as the IdP to check device management enrollment, ideal for BYOD or remote workforces.

### [Shared Signals Framework (SSF) support](../add-secure-apps/providers/ssf/index.md)

The SSF Provider enables authentik to transmit real-time security events (e.g., MFA changes, logouts) as Security Event Tokens to subscribed OIDC applications via secure webhooks. Also allows for integration with Apple Business Manager (ABM).

### [Password history compliance checks](../customize/policies/types/password-uniqueness.md)

The Password Uniqueness Policy blocks reuse of previous passwords by comparing new ones against stored hashes of previous passwords.

### [Client certificate authentication (mTLS)](../add-secure-apps/flows-stages/stages/mtls/index.md)

The Mutual TLS stage uses client certificates (from devices, PIV cards, or Yubikeys) signed by private CAs for user enrollment and authentication. Configurable modes allow optional or required certificates, matching attributes like username or email.
