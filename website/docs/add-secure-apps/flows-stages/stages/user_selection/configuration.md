---
title: Configure user selection stages
---

## Configuration options

### User Selection stage

- **Name**: the name used to identify the stage in the admin interface.

## Flow integration

User selection stages should be bound to a flow with the **User Selection** designation.

A typical user-selection flow contains a single User Selection stage. When users choose a different remembered account, authentik starts the normal authentication flow with that user pre-filled. The active browser session is not changed until authentication succeeds.

## Brand integration

Each brand can select a user-selection flow. When configured, authentik uses the brand's flow for:

- the user switcher in the user interface;
- OpenID Connect authorization requests with `prompt=select_account`;
- OpenID Connect authorization requests where the browser has multiple remembered accounts.

If no brand flow is configured, authentik falls back to the first applicable flow with the **User Selection** designation.

## Notes

### Account hints

When a flow starts with a login hint, authentik places the matching remembered account first. The hint does not authenticate the account by itself; the user must still choose an account and complete authentication when selecting a non-current user.

OpenID Connect providers can trigger this behavior with `prompt=select_account`. They can also send `login_hint` to suggest which remembered account should appear first.

### Adding another account

When the user chooses to use another account, authentik starts the default authentication flow without a pre-filled remembered user. Existing sessions remain unchanged until the new authentication flow succeeds.
