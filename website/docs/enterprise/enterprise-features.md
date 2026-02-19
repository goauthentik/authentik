---
title: Enterprise features
description: "The extra features that are included in authentik Enterprise"
---

This page describes the Enterprise features that are available in the authentik [Enterprise plans](https://goauthentik.io/pricing/).

## Enterprise vs Enterprise Plus

Enterprise Plus differs from Enterprise in that Plus offers the following options:

- Billing and purchase via invoice
- Dedicated, customized support and SLAs
- Volume discounts at thousands of users
- FIPS compliance for FedRAMP requirements

Both Enterprise and Enterprise Plus plans include all the following features:

## Features

### Enhanced logging

#### Enhanced audit logging for compliance

Enhanced audit logging captures detailed model changes with "before" and "after" states, including many-to-many relationships, for comprehensive compliance tracking.

[Enhanced audit logging](../sys-mgmt/events/logging-events.mdx#enhanced-audit-logging)

#### Viewing logs in maps and charts

View recent events on both a world map view with pinpoints indicating where each event occurred and also a color-coded chart that highlights event types and volume.

[Viewing events in maps and charts](../sys-mgmt/events/logging-events.mdx#viewing-events-in-maps-and-charts)

#### Exporting logs

You can export authentik event logs to a CSV file.

[Export events](../sys-mgmt/events/logging-events.mdx#export-events)

#### Advanced queries

Allows you to construct advanced queries to find specific event logs using syntax similar to DjangoQL.

[Advanced queries for event logs](../sys-mgmt/events/logging-events.mdx#advanced-queries)

### Google Workspace integration

The Google Workspace provider syncs users and groups from authentik to Google Workspace, making authentik the source of truth. It supports direct syncs for real-time changes and automatically linking existing entities.

[Google Workspace Provider](../add-secure-apps/providers/gws/index.md)

### Microsoft Entra ID integration

The Microsoft Entra ID provider synchronizes users and groups from authentik to Microsoft Entra ID, making authentik the source of truth. It supports direct syncs for real-time changes and automatically linking existing entities.

[Microsoft Entra ID Provider](../add-secure-apps/providers/entra/index.md)

### Embed external OAuth/SAML sources

The Source Stage embeds external OAuth or SAML providers into authentik flows for dynamic user verification. It enables integration with legacy IdPs (e.g., Okta) during migrations.

[Source Stage](../add-secure-apps/flows-stages/stages/source/index.md)

### Chrome Enterprise Device Trust connector

This authenticator stage validates Chrome browsers and ChromeOS devices against enterprise policies, ensuring compliance before access. It integrates authentik as the IdP to check device management enrollment, ideal for BYOD or remote workforces.

[Google Chrome Device Trust Authenticator Stage](../add-secure-apps/flows-stages/stages/authenticator_endpoint_gdtc/index.md)

### Shared Signals Framework (SSF) support

The SSF Provider enables authentik to transmit real-time security events (e.g., MFA changes, logouts) as Security Event Tokens to subscribed OIDC applications via secure webhooks. Also allows for integration with Apple Business Manager (ABM).

[Shared Signals Framework (SSF) Provider](../add-secure-apps/providers/ssf/index.md)

### Password history compliance checks

The Password Uniqueness Policy blocks reuse of previous passwords by comparing new ones against stored hashes of previous passwords.

[Password Uniqueness Policy](../customize/policies/unique_password.md)

### Client certificate authentication (mTLS)

The Mutual TLS stage uses client certificates (from devices, PIV cards, or Yubikeys) signed by private CAs for user enrollment and authentication. Configurable modes allow optional or required certificates, matching attributes like username or email.

[Mutual TLS stage](../add-secure-apps/flows-stages/stages/mtls/index.md)
