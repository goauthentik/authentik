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
- A **[device access group](../device-access-groups.mdx)** configured with the appropriate user or group bindings. Without this group, all login attempts are denied. See [Configure device access](#configure-device-access).

## How it works

- authentik Agent is integrated with the Pluggable Authentication Modules (PAM) framework on the Linux device.
- The end user logs in via the usual Linux login screen and is prompted for their authentik credentials.
- The Agent authenticates the credentials against the authentik server and the user is logged in.

## How to log in to a Linux device

:::note
When configured correctly, when you log in you should see a prompt for **authentik Password** rather than just **Password**.
:::

1. On the Linux login screen, you enter your authentik credentials.
2. After you authenticate, you are logged in to the Linux device.

## Configure device access

Local device login requires the authenticating user to have access to the device. [Device access groups](../device-access-groups.mdx) always control access. On Enterprise, direct device bindings for users, groups, or policies also affect access. Without an appropriately configured device access group or direct binding, **all login attempts are denied**.

1. In the Admin interface, navigate to **Endpoint Devices** > **Device access groups** and click **New Device Access Group**.
2. Provide a **Group name** (e.g. `linux-devices`) and click **Create Device Access Group**.
3. Expand the newly created device access group and click **Bind existing Policy / Group / User**.
4. Select **Group** and choose a group that contains the users who should be allowed to log in to the device. Alternatively, bind a specific **User** or a **Policy**.
5. Click **Create**.
6. Navigate to **Endpoint Devices** > **Devices** and edit the device for which you want to enable login.
7. Set the **Access group** to the device access group you created.
8. Click **Update**.

:::info
You can also assign a device access group during enrollment by selecting a **Device group** when creating the enrollment token.
:::

## Known issues

- Only WebAuthn MFA is supported.
- On non-Debian Linux distributions, you currently need to [manually configure NSS and PAM](../../agent-deployment/linux.mdx#configure-device-login-on-non-debian-systems).
