---
title: Deploy authentik Agent on macOS
sidebar_label: macOS
tags: [authentik Agent, mac, macos, deploy]
---

## What it can do

- Retrieves information about the host for use in authentik, see [Device Compliance](../../device-compliance/index.mdx).
- SSH to Linux hosts using authentik credentials, see [SSH authentication](../../device-authentication/ssh-authentication.mdx).
- Authenticate CLI applications using authentik credentials, see [CLI application authentication](../../device-authentication/cli-app-authentication/index.mdx).

## Prerequisites

You must [configure your authentik deployment](../configuration.md) to support the authentik Agent.

## Create an enrollment token

If you have already created have an enrollment token, skip to the [next section](#install-the-authentik-agent-on-macos).

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**.
3. Click on the authentik Agent connector that you created when [configuring your authentik deployment](../configuration.md) to support the authentik agent.
4. Under **Enrollment Tokens**, click **Create**, and configure the following settings:
    - **Token name**: provide a descriptive name for the token
    - **Device group _(optional)_**: select a device access group for the device to be added to after completing enrollment
    - **Expiring _(optional)_**: set whether or not the enrollment token will expire
5. Click **Create**.
6. _(Optional)_ Click the **Copy** icon in the **Actions** column to copy the enrollment token. This value will be required if [enabling a device for device compliance](#enable-device-compliance).

## Install the authentik Agent on macOS

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**.
3. Click on the authentik Agent connector that you created when [configuring your authentik deployment](../configuration.md) to support the authentik agent.
4. Under **Setup**, click **macOS** to download the authentik Agent installer.
5. Once the download is complete, attempt to install the package. Default Apple security settings should block the install.
    - This can be avoided by Option + Right Clicking the package and clicking **Open**.
    - Alternatively use the following command to remove the package from quarantine: `xattr -r -d com.apple.quarantine "$HOME/Downloads/authentik agent installer.pkg"`
6. Confirm that the authentik Agent is installed by opening a Terminal window and entering the following command: `ak`
   You should see a response that starts with: `authentik CLI v<version_number>`

## Enable device authentication

To enable [device authentication features](../../device-authentication/index.mdx), you must connect the device to an authentik deployment. To do so, follow these steps:

1. Open a Terminal session and run the following command:

```sh
ak config setup --authentik-url https://authentik.company
```

2. Your default browser will open and direct you to the authentik login page. Once authenticated, the authentik Agent will be configured.

## Enable device compliance

To enable [device compliance features](../../device-compliance/index.mdx), you must join the device to an authentik domain.

1. Open a Terminal session and run the following command:

```sh
"/Applications/authentik Agent.app/Contents/MacOS/ak-sysd" domains join <deployment_name> --authentik-url https://authentik.company
```

- `deployment_name` is the name that will be used to identify the authentik deployment on the device.
- `https://authentik.company` is the fully qualified domain name of the authentik deployment.

2. You will be prompted to enter your [enrollment token](#create-an-enrollment-token).
3. Once provided, the device will be enrolled with your authentik deployment and should appear on the [Devices page](../../manage-devices.mdx) after a [check-in](../../device-compliance/device-reporting.md) is completed.

## Logging

The authentik Agent uses macOS's native logging abilities. To retrieve the logs, open the Console application and then filter for authentik-related processes such as `authentik-agent` or `authentik-sysd`.
