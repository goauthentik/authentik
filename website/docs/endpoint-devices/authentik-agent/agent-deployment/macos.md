---
title: Deploy authentik Agent on macOS
sidebar_label: macOS
tags: [authentik Agent, mac, macos, deploy]
authentik_version: "2025.12.0"
---

## What it can do

- Retrieve host information and report it to authentik for [device compliance](../../device-compliance/index.mdx).
- Connect to Linux hosts through [SSH authentication](../../authentik-agent/device-authentication/ssh-authentication.mdx).
- Authenticate to CLI applications through [CLI application authentication](../../authentik-agent/device-authentication/cli-app-authentication/index.mdx).

## Prerequisites

You must [configure your authentik deployment](../configuration.md) to support the authentik Agent.

## Create an enrollment token

If you already have an enrollment token, skip to the [next section](#install-the-authentik-agent-on-macos).

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**.
3. Click on the authentik Agent connector that you created when [configuring your authentik deployment](../configuration.md) to support the authentik agent.
4. Under **Enrollment Tokens**, click **New Enrollment Token**, and configure the following settings:
    - **Token name**: Provide a descriptive name for the token.
    - **Device group _(optional)_**: Select a device access group to add the device to after enrollment.
    - **Expiring _(optional)_**: Set whether the enrollment token expires.
5. Click **Create**.
6. _(Optional)_ Click the **Copy** icon in the **Actions** column. You need this value to [enable device compliance](#enable-device-compliance).

## Install the authentik Agent on macOS

:::info Automated deployment is recommended
It's recommended to deploy the Agent via [MDM or automation tools](./automated.mdx) instead of manually configuring it.
:::

:::info Serial number required
The Agent requires a serial number be presented by macOS. Some hypervisors don't set serial numbers. When deploying on a virtual machine, ensure that it has a serial number set.
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**.
3. Click on the authentik Agent connector that you created when [configuring your authentik deployment](../configuration.md) to support the authentik agent.
4. Under **Setup**, click **macOS** to download the authentik Agent installer.
5. After the download completes, attempt to install the package. Default Apple security settings should block the installation.
    - This can be avoided by Option + Right Clicking the package and clicking **Open**.
    - Alternatively use the following command to remove the package from quarantine: `xattr -r -d com.apple.quarantine "$HOME/Downloads/authentik agent installer.pkg"`
6. Confirm that the authentik Agent is installed by opening a Terminal window and entering the following command: `ak`

    You should see a response that starts with: `authentik CLI v<version_number>`

## Enable device compliance

To enable [device compliance features](../../device-compliance/index.mdx), you must join the device to an authentik domain.

1. Open a Terminal session and run the following command:

```sh
sudo "/Applications/authentik Agent.app/Contents/MacOS/ak-sysd" domains join <deployment_name> --authentik-url https://authentik.company
```

- `deployment_name` identifies the authentik deployment on the device.
- `https://authentik.company` is the fully qualified domain name of the authentik deployment.

2. Enter your [enrollment token](#create-an-enrollment-token) when prompted.
3. After you enter the token, authentik enrolls the device. The device appears on the [Devices page](../../manage-devices.mdx) after it [checks in](../../device-compliance/device-reporting.md).

## Enable SSH client authentication and CLI application authentication

To enable [initiating SSH connections](../../authentik-agent/device-authentication/ssh-authentication.mdx) and [CLI application authentication](../../authentik-agent/device-authentication/cli-app-authentication/index.mdx), the device must be connected to an authentik deployment. To do so, follow these steps:

1. Open a Terminal session and run the following command:

```sh
ak config setup --authentik-url https://authentik.company
```

2. Your default browser opens the authentik login page. After you authenticate, the authentik Agent is configured.

## Check version of installed components

You can check the version of all installed authentik components by running the following command:

```bash
ak version
```

## View logs

The authentik Agent uses macOS's native logging abilities. To retrieve the logs, open the Console application and then filter for authentik-related processes such as `authentik-agent` or `authentik-sysd`.

## Report issues

Please report issues and bugs via the [authentik Platform GitHub repository](https://github.com/goauthentik/platform).
