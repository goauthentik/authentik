---
title: Enterprise features
description: "The extra features that are included in authentik Enterprise"
---

This page describes the Enterprise features that are available in the authentik [Enterprise plans](https://goauthentik.io/pricing/).

## Enterprise vs Enterprise Plus

The Enterprise release of authentik is available in two tiers: Enterprise and Enterprise+.

Enterprise builds on authentik's open-source foundation with enterprise-grade features and ticket-based support.

Enterprise+ is designed to provide the best overall end-user experience while mitigating risk and delivering the fastest time-to-value. It includes everything in Enterprise, plus onboarding best practices, dedicated support channels (Slack and/or scheduled video calls for complex issues) with SLA-backed response times, volume discounts, and support for FIPS-compliant deployments to meet FedRAMP-aligned requirements. It also supports billing and purchase via invoice.

Both Enterprise and Enterprise Plus plans include all the following features:

## Features

### Enhanced logging

#### [Enhanced audit logging for compliance](../sys-mgmt/events/logging-events.mdx#enhanced-audit-logging)

Enhanced audit logging captures detailed model changes with "before" and "after" states, including many-to-many relationships, for comprehensive compliance tracking.

#### [Viewing logs in maps and charts](../sys-mgmt/events/logging-events.mdx#viewing-events-in-maps-and-charts)

View recent events on both a world map view with pinpoints indicating where each event occurred and also a color-coded chart that highlights event types and volume.

#### [Exporting logs](../sys-mgmt/events/logging-events.mdx#export-events)

You can export authentik event logs to a CSV file.

#### [Advanced queries](../sys-mgmt/events/logging-events.mdx#advanced-queries)

Allows you to construct advanced queries to find specific event logs using syntax similar to DjangoQL.

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

### [Password history compliance checks](../customize/policies/unique_password.md)

The Password Uniqueness Policy blocks reuse of previous passwords by comparing new ones against stored hashes of previous passwords.

### [Client certificate authentication (mTLS)](../add-secure-apps/flows-stages/stages/mtls/index.md)

The Mutual TLS stage uses client certificates (from devices, PIV cards, or Yubikeys) signed by private CAs for user enrollment and authentication. Configurable modes allow optional or required certificates, matching attributes like username or email.
