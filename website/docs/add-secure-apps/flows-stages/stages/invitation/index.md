---
title: Invitation stage
---

The Invitation stage lets an enrollment flow require an invitation token and optionally pre-fill or enforce fixed enrollment data.

## Overview

This stage is typically used in enrollment flows where users should only be allowed to continue if they were invited.

An invitation can also carry fixed data that is applied during enrollment.

## Configuration options

- **Continue flow without invitation**: if enabled, the flow continues when no invitation token is present. If disabled, the flow stops when the token is missing.

## Flow integration

Add this stage near the beginning of an enrollment flow that should be invitation-gated.

Users can enter the flow with an invitation token by using a URL like:

```text
https://authentik.example/if/flow/your-enrollment-flow/?itoken=invitation-token
```

You can also collect the token with a [Prompt stage](../prompt/index.md) by using a prompt field with the key `token`.

## Notes

- In policies, you can check whether an invitation is active with `request.context.get("invitation_in_effect", False)`.
- Invitation objects can be restricted to a specific flow and can be marked as single-use.
