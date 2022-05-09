---
title: User login stage
---

This stage attaches a currently pending user to the current session.

It can be used after `user_write` during an enrollment flow, or after a `password` stage during an authentication flow.

## Session duration

By default, the authentik session expires when you close your browser (_seconds=0_).

You can set the session to expire after any duration using the syntax of `hours=1,minutes=2,seconds=3`. The following keys are allowed:

-   Microseconds
-   Milliseconds
-   Seconds
-   Minutes
-   Hours
-   Days
-   Weeks

All values accept floating-point values.
