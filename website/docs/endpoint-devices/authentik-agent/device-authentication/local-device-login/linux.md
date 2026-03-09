---
title: Linux local device login
sidebar_label: Linux
tags: [authentik Agent, device login, device authentication, linux]
authentik_enterprise: true
authentik_version: "2025.12.0"
---

<!-- TODO @BeryJu add screenshot -->

## Prerequisites

- The authentik Agent deployed on the Linux device. See [Deploy the authentik Agent on Linux](../../agent-deployment/linux.mdx) for more details.
- A **[Device access group](../device-access-groups.mdx)** configured with the appropriate user or group bindings. Without this, all login attempts will be denied. See [Configure device access](#configure-device-access) below.

## How it works

- authentik Agent is integrated with the Pluggable Authentication Modules (PAM) framework on the Linux device.
- The end user logs in via the usual Linux login screen but are prompted for their authentik credentials.
- The Agent authenticates the credentials against the authentik server and the user is logged in.

## How to log in to a Linux device

:::note
When configured correctly, when logging in you should see a prompt for **authentik Password** rather than just **Password**.
:::

1. On the Linux login screen, you enter your authentik credentials.
2. Once authenticated, you will be logged in to the Linux device.

## Configure device access

Local device login requires that the authenticating user is authorized to access the device. Access is controlled via [device access groups](../device-access-groups.mdx). If no device access group is configured with the appropriate bindings, **all login attempts will be silently denied**.

1. Navigate to **Endpoint Devices** > **Device access groups** and click **Create**.
2. Provide a **Group name** (e.g. `linux-devices`) and click **Create**.
3. Expand the newly created device access group and click **Bind existing Policy / Group / User**.
4. Select **Group** and choose a group that contains the users who should be allowed to log in to the device. Alternatively, bind a specific **User** or a **Policy**.
5. Click **Create**.
6. Navigate to **Endpoint Devices** > **Devices** and edit the device you want to enable login for.
7. Set the **Access group** to the device access group you created.
8. Click **Update**.

:::info
You can also assign a device access group during enrollment by selecting a **Device group** when creating the enrollment token.
:::

## Known issues

- Only Webauthn MFA is supported.
- On non-Debian Linux distributions, you currently need to [manually configure NSS and PAM](../../agent-deployment/linux.mdx#configure-device-login-on-non-debian-systems).
