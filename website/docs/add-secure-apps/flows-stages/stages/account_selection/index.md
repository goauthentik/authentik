---
title: Account selection stages
---

The Account Selection and Account Switch stages let users choose between live accounts that are already known in the same browser.

## Overview

authentik remembers accounts in a signed browser cookie after login. The Account Selection stage reads that browser-local list, filters out stale sessions, and shows the user the current account plus any other remembered accounts that still have a live authentik session.

The Account Switch stage activates the account selected by an earlier Account Selection stage. Keeping the switch as a separate stage lets you insert other stages between selection and activation, such as an Authenticator Validation stage to require MFA before switching accounts.

The default account-selection flow contains:

1. An Account Selection stage.
2. An Account Switch stage.

The default brand uses this flow for account switching and OpenID Connect `prompt=select_account` requests.

## Configuration options

### Account Selection stage

- **Name**: the name used to identify the stage in the admin interface.

### Account Switch stage

- **Name**: the name used to identify the stage in the admin interface.

## Flow integration

Use these stages in a flow with the **Account Selection** designation.

For normal account switching, bind the stages in this order:

1. Account Selection stage.
2. Optional verification stages, such as [Authenticator Validation](../authenticator_validate/index.md).
3. Account Switch stage.

The Account Selection stage stores the selected account in the flow context. The Account Switch stage then verifies that the remembered session still exists and belongs to the selected active user before it changes the browser's primary authentik session cookie.

## Brand integration

Brands can select an account-selection flow. When configured, authentik uses that brand flow for:

- the account switcher in the user interface
- OpenID Connect authorization requests with `prompt=select_account`
- OpenID Connect authorization requests where the browser has multiple live remembered accounts

If no brand-specific flow is configured, authentik falls back to the first applicable flow with the **Account Selection** designation.

## Notes

### Requiring MFA on account switch

To require MFA before a remembered account becomes active, insert an Authenticator Validation stage between the Account Selection and Account Switch stages.

The selected account is set as the pending user before the MFA stage runs, so authenticator policies and device lookups evaluate against the account that will be switched to.

### Account hints

When an account-selection flow is started with a login hint, authentik places the matching remembered account first and treats it as the primary action. The hint does not by itself switch accounts; the user must still choose the account unless an explicit account identifier is supplied by authentik's own account switcher.

### Adding another account

When the user chooses to add another account, authentik starts the default authentication flow in a fresh anonymous browser session. The existing remembered sessions remain available so the user can switch back later.
