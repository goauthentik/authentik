---
title: Control user access
sidebar_position: 8
---

authentik provides several controls that can restrict a user's access. Choose a control based on the access that must be stopped and how the restriction should be cleared.

Controls can overlap. The user status shows the highest-priority restriction in this order: deactivated, password login locked, password reset pending, and active. Clearing one restriction does not clear the others.

| Control                                                                 | Effect                                                                                                                                                                        | User status                                                 | Restore access                                                            |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Lock password login** :ak-enterprise                                  | Blocks authentication through Password stages. Existing sessions, tokens, and other authentication methods remain available.                                                  | **Locked**                                                  | Click **Unlock password login**.                                          |
| [**Force password reset on next login**](./password_reset_on_login.mdx) | Uses an authentication flow and user attribute to require a password change. It does not otherwise restrict access.                                                           | **Password reset pending**                                  | Complete the password-change flow or clear the configured user attribute. |
| **Deactivate**                                                          | Disables the authentik user. Existing sessions are revoked, and the inactive state can be propagated to connected systems.                                                    | **Deactivated**                                             | Click **Activate**.                                                       |
| [**Account Lockdown**](../../security/account-lockdown.md)              | Runs an emergency response flow. Depending on its configuration, it can deactivate the user, invalidate the password, revoke sessions and tokens, and create an audit event.  | Usually **Deactivated** when the flow deactivates the user. | Restore each state changed by the configured lockdown flow.               |
| [**Reputation policy**](../../customize/policies/types/reputation.md)   | Evaluates a username, client IP address, or both against a reputation score. A failed policy can block a request or select an additional challenge without changing the user. | Unchanged                                                   | Allow the reputation score to expire, adjust it, or change the policy.    |

For password lockout thresholds and user messages, see the [Password stage](../../add-secure-apps/flows-stages/stages/password/index.md) documentation. For administrative user actions, see [User basic operations](./user_basic_operations.md).
