---
title: Configure account selection stages
---

## Configuration options

### Account Selection stage

- **Name**: the name used to identify the stage in the admin interface.

### Account Switch stage

- **Name**: the name used to identify the stage in the admin interface.

## Flow integration

Account selection stages should be bound to a flow with the **Account Selection** designation.

A typical account-selection flow uses this order:

1. Account Selection stage.
2. Optional verification stages, such as [Authenticator Validation](../authenticator_validate/index.md).
3. Account Switch stage.

The Account Selection stage stores the selected account in the flow context. The Account Switch stage validates that the remembered session still exists, belongs to the selected active user, and is safe to activate before changing the browser's primary authentik session.

## Brand integration

Each brand can select an account-selection flow. When configured, authentik uses the brand's flow for:

- the account switcher in the user interface;
- OpenID Connect authorization requests with `prompt=select_account`;
- OpenID Connect authorization requests where the browser has multiple live remembered accounts.

If no brand flow is configured, authentik falls back to the first applicable flow with the **Account Selection** designation.

## Notes

### Requiring MFA on account switch

To require MFA before an account switch, insert an [Authenticator Validation stage](../authenticator_validate/index.md) between the Account Selection stage and the Account Switch stage.

The selected account is set as the pending user before the validation stage runs. Authenticator policies and device lookups therefore evaluate against the account that will become active.

### Account hints

When a flow starts with a login hint, authentik places the matching remembered account first. The hint does not switch accounts by itself; the user must still choose an account unless authentik starts the flow from its own account switcher with an explicit account identifier.

OpenID Connect providers can trigger this behavior with `prompt=select_account`. They can also send `login_hint` to suggest which remembered account should appear first.

### Adding another account

When the user chooses to use another account, authentik starts the default authentication flow in a fresh anonymous browser session. Existing remembered sessions remain available so the user can switch back later.
