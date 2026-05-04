---
title: Reputation Policy
tags:
    - policy
    - reputation
    - security
---

Use a Reputation policy when you want authentik to react to repeated failed authentication attempts from a username, a client IP, or both.

## How reputation works

authentik tracks a reputation score over time:

- failed logins decrease the score
- successful logins increase the score

The policy passes when the score is at or below the configured threshold.

In practice, this is usually used to show an extra challenge only when a request looks risky. For example, you can bind a CAPTCHA stage so it runs only for low-reputation requests.

## What it can check

A Reputation policy can evaluate:

- the client IP
- the username
- both together

The threshold defaults to a low score, so the policy is naturally suited to "trigger extra verification when trust is low" scenarios.

## Create a Reputation policy

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **New Policy** and select **Reputation Policy**.
4. Choose whether to check IP, username, or both, and set the threshold.
5. Click **Create Policy**.

## Use it on stage bindings

When you use a Reputation policy on a flow stage binding, configure the stage binding to **Evaluate when stage is run** so authentik can use the latest request context.

This is especially important when the policy should react to the current login attempt rather than only to the initial planned flow state.

## Related settings

System-wide reputation limits and expiry are documented in [Settings](../../../sys-mgmt/settings.md).
