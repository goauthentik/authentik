---
title: User selection stage
---

The user selection stage lets users choose which remembered authentik account should continue a flow.

## Overview

authentik can remember multiple accounts within the same browser. The list of remembered accounts is stored in a signed browser cookie.

The stage has one responsibility:

- **User Selection stage**: shows the current account and other remembered accounts.

Selecting the current account continues the flow. Selecting another remembered account starts normal authentication with that account pre-filled; authentik does not activate another stored session.

authentik includes a default user-selection flow and assigns it to the default brand. The flow is used by the user interface account switcher and by OpenID Connect requests that need user selection.

For setup details, see [Configure user selection stages](configuration.md).
