---
title: Next release
---

## Headline Changes

- Simplify role-based access

    Instead of having to create a Group Membership policy for every group you want to use, you can now select a Group and even a User directly in a binding.

    When a group is selected, the binding behaves the same as if a Group Membership policy exists.

    When a user is selected, the binding checks the user of the request, and denies the request when the user doesn't match.

