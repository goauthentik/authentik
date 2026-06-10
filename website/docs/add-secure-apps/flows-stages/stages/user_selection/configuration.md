---
title: Configure user selection stages
---

## Configuration options

### User Selection stage

- **Name**: the name used to identify the stage in the admin interface.

## Flow integration

User selection stages should be bound to a flow with the **User Selection** designation.

A typical user-selection flow contains a single User Selection stage. The stage lists active sessions bound to the same browser. If the request is already authenticated, the user can continue with the current account or switch to another live browser-local session. If the request is signed out, selecting an account starts normal authentication with that account pre-filled.

## Brand integration

Each brand can select a user-selection flow. When configured, authentik uses the brand's flow for:

- the account switcher in the user interface;
- OpenID Connect authorization requests with `prompt=select_account`;
- OpenID Connect authorization requests where the browser has multiple live accounts.

The account switcher needs the brand flow to be configured so it has a specific flow to open. Server-started account selection, such as OpenID Connect account selection, falls back to the first applicable flow with the **User Selection** designation if the brand does not configure one.

## Notes

### Account hints

When a flow starts with a login hint, authentik places the matching browser-local account first. The hint does not authenticate the account by itself; the user must still choose the account. If the browser is already authenticated, authentik can switch to another live session for that browser. If the browser is signed out, authentik starts normal authentication with the hinted account pre-filled.

OpenID Connect clients can trigger this behavior with `prompt=select_account`. They can also send `login_hint` to suggest which browser-local account should appear first.

### Adding another account

When the user chooses to use another account, authentik starts the default authentication flow without a pre-filled user. Existing sessions remain available while the new account authenticates in its own session.
