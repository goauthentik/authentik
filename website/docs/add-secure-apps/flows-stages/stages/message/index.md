---
title: Message stage
authentik_version: "2026.8"
---

The message stage presents a custom message that the user dismisses before continuing through a flow.

## Overview

Use this stage to display a message or information such as instructions or application-specific notifications. Policies can be bound to the stage to display a message only when specific conditions are met.

## Configuration options

- **Title**: optional heading displayed above the message.
- **Message**: content displayed to the user. Basic HTML is supported.
- **Button text**: optional label for the acknowledgment button. If this field is empty, the button displays **Continue**.

## Flow integration

Use this stage anywhere a message needs to be presented to the user.

Common useful cases for displaying a message stage include:

- Informing the user that their account has been activated.
- Informing the user that an action has occurred.
- Informing the user of upcoming maintenance or downtime.

When the flow reaches the binding, the message appears as a separate card. After the user acknowledges the message, the flow advances to the next stage.

## Display a message conditionally

Bind a policy to the stage binding when the message should appear only under specific conditions. For example, an expression policy can limit a maintenance notification to a scheduled time period or to requests for a specific application.

For more information, see [Bind a policy to a stage](../../../../customize/policies/working_with_policies.md#bind-a-policy-to-a-stage-binding) and [Planning and stage policies](../../flow/planner.md#planning-and-stage-policies).

## Notes

- The message appears only while the message stage is active. It does not remain visible on subsequent flow cards.
- Clicking the acknowledgment button does not store an acknowledgment record. Use a [consent stage](../consent/index.md) when intending to record and reuse a user's consent.
