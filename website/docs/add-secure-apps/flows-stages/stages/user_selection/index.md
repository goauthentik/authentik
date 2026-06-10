---
title: User selection stage
---

The user selection stage lets users choose which browser-local authentik account should continue a flow.

## Overview

authentik can keep multiple live accounts available within the same browser. Each login has its own session, and authentik binds those sessions to an opaque browser cookie so only the same browser can list or switch to them.

The stage has one responsibility:

- **User Selection stage**: shows the current account and other live accounts for the same browser.

Selecting the current account continues the flow. When the request is already authenticated, selecting another live account switches the active browser session to that account. When the request is signed out, selecting a browser-local account starts the default authentication flow with that account pre-filled.

authentik includes a default user-selection flow and assigns it to the default brand. The flow is used by the user interface account switcher, by OpenID Connect requests with `prompt=select_account`, and by OpenID Connect requests where the browser has multiple live accounts.

For setup details, see [Configure user selection stages](configuration.md).
