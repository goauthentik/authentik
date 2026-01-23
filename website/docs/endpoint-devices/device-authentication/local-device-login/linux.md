---
title: Linux local device login
sidebar_label: Linux
tags: [authentik Agent, device login, device authentication, linux]
authentik_enterprise: true
---

<!-- TODO @BeryJu add screenshot -->

## Prerequisites

You need to have deployed the authentik Agent on the Linux device, see [Deploy the authentik Agent on Linux](../../authentik-agent/agent-deployment/linux.md) for more details.

## How it works

- authentik Agent is integrated with the Pluggable Authentication Modules (PAM) framework on the Linux device.
- The end user logs in via the usual Linux login screen but are prompted for their authentik credentials.
- The Agent authenticates the credentials against the authentik server and the user is logged in.

## How to log in to a Linux device

1. On the Linux login screen, you enter your authentik credentials.
2. Once authenticated, you will be logged in to the Linux device.

## Known issues

- On non-Debian Linux distibutions, you will need to manually configure PAM.
- MFA is supported except for Webauthn.
