---
title: User login stage
---

This stage attaches a currently pending user to the current session.

It can be used after `user_write` during an enrollment flow, or after a `password` stage during an authentication flow.

## Session duration

By default, the authentik session expires when you close your browser (_seconds=0_).

:::warning
Different browsers handle session cookies differently, and might not remove them even when the browser is closed. See [here](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#expiresdate) for more info.
:::

You can set the session to expire after any duration using the syntax of `hours=1,minutes=2,seconds=3`. The following keys are allowed:

-   Microseconds
-   Milliseconds
-   Seconds
-   Minutes
-   Hours
-   Days
-   Weeks

All values accept floating-point values.

## Stay signed in offset

When this is set to a higher value than the default _seconds=0_, a prompt is shown, allowing the users to choose if their session should be extended or not. The same syntax as for _Session duration_ applies.

![](./stay_signed_in.png)

## Terminate other sessions

When enabled, previous sessions of the user logging in will be revoked. This has no affect on OAuth refresh tokens.
