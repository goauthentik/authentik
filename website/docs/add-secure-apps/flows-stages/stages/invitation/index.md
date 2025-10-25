---
title: Invitation stage
---

This stage can be used to invite users. You can use this to enroll users with preset values.

If the option `Continue Flow without Invitation` is enabled, this stage will continue even when no invitation token is present.

To check if a user has used an invitation within a policy, you can check `request.context.get("invitation_in_effect", False)`.

To use an invitation, use the URL `https://authentik.tld/if/flow/your-enrollment-flow/?itoken=invitation-token`.

You can also prompt the user for an invite by using the [_Prompt stage_](../prompt/index.md) by using a field with a field key of `token`.
