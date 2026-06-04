---
title: Account selection stage
---

The account selection stage allows users choose which remembered authentik account should continue a flow.

## Overview

authentik can remember multiple accounts within the same browser. The list of remembered accounts is stored in a signed browser cookie, and an account only appears if its authentik session is still active.

Two stages work together:

- **Account Selection stage**: shows the current account and other live remembered accounts.
- **Account Switch stage**: activates the account selected by the Account Selection stage.

Keeping selection and activation separate lets you add verification stages between them. For example, you can require MFA before the selected account becomes the active browser session.

authentik includes a default account-selection flow and assigns it to the default brand. The flow is used by the user interface account switcher and by OpenID Connect requests that need account selection.

For setup details, see [Configure account selection stages](configuration.md).
