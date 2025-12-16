---
title: Deploy authentik Agent on Windows
sidebar_label: Windows
tags: [authentik Agent, windows]
---

## What it can do

- Retrieves information about the host for use in authentik, see [Device Compliance](../../device-compliance/index.mdx).
- SSH to Linux hosts using authentik credentials, see [SSH authentication](../../device-authentication/ssh-authentication.mdx).
- Authenticate CLI applications using authentik credentials, see [CLI application authentication](../../device-authentication/cli-app-authentication/index.mdx).

:::warn Supported Windows Versions
The authentik Agent is currently only tested on Windows 11 and Windows Server 2022. Other versions may work but are untested.
:::

## Prerequisites

You must [configure your authentik deployment](../configuration.md) to support the authentik Agent.

## Create an enrollment token

If you have already created have an enrollment token, skip to the [next section](#install-the-authentik-agent-on-windows).

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**.
3. Click on the authentik Agent connector that you created when [configuring your authentik deployment](../configuration.md) to support the authentik agent.
4. Under **Enrollment Tokens**, click **Create**, and configure the following settings:
    - **Token name**: provide a descriptive name for the token
    - **Device group _(optional)_**: select a device access group for the device to be added to after completing enrollment
    - **Expiring _(optional)_**: set whether or not the enrollment token will expire
5. Click **Create**.
6. _(Optional)_ Click the **Copy** icon in the **Actions** column to copy the enrollment token. This value will be required if [enabling a device for device compliance](#enable-device-compliance).

## Install the authentik Agent on Windows

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**.
3. Click on the authentik Agent connector that you created when [configuring your authentik deployment](../configuration.md) to support the authentik agent.
4. Under **Setup**, click **Windows** to download the authentik Agent installer.
5. Once the download is complete, install the MSI file.
6. _(Optional)_ During installation, select [Windows Credential Provider](#windows-credential-provider) if you want to log in to the Windows device using authentik credentials.
7. Confirm that the authentik Agent is installed by opening a PowerShell or Terminal window and entering the following command: `ak`
   You should see a response that starts with: `authentik CLI v<version_number>`

## Enable device authentication

To enable [device authentication features](../../device-authentication/index.mdx), you must connect the device to an authentik deployment. To do so, follow these steps:

1. Open a Terminal and run the following command:

```sh
ak config setup --authentik-url https://authentik.company
```

2. Your default browser will open and direct you to the authentik login page. Once authenticated, the authentik Agent will be configured.

## Enable device compliance

To enable [device compliance features](../../device-compliance/index.mdx), you must join the device to an authentik domain. This can be done via the CLI or by editing a configuration file.

### CLI

1. Open a Terminal session and run the following command:

```sh
ak-sysd domains join <deployment_name> --authentik-url https://authentik.company
```

- `deployment_name` is the name that will be used to identify the authentik deployment on the device.
- `https://authentik.company` is the fully qualified domain name of the authentik deployment.

2. You will be prompted to enter your [enrollment token](#create-an-enrollment-token).
3. Once provided, the device will be enrolled with your authentik deployment and should appear on the [Devices page](../../manage-devices.mdx) after a [check-in](../../device-compliance/device-reporting.md) is completed.

### Configuration file

1. Create the following file: (TODO) windows filepath
2. Paste the following values into the file:

(TODO) JSON codeblock

## Windows Credential Provider

Windows Credential Provider (WCP) is a component of the authentik Agent that allows logging in to Windows workstations using authentik credentials.

It currently only supports local login; RDP login is not supported.

:::warning

- When WCP is enabled, the password of the Windows user account that's used to login is set to a random string.
- WCP can cause issues with user encrypted directories.
- Support with Active directory has not been confirmed yet.
- Offline login is currently not supported.
  :::

#### Configure Windows Credential Provider

You'll need to add a registry entry for WCP to work:

1. On the Windows device, open the Notepad application.
2. Paste the following block of text into Notepad:

```powershell
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\CLSID\{7BCC7941-18BA-4A8E-8E0A-1D0F8E73577A}]
"URL"="https://authentik.company"
"ClientID"="authentik-cli"
```

Where `URL` is the FQDN of your authentik deployment and `ClientID` is the Client ID of the [`authentik-cli` provider](../configuration.md#create-an-application-and-provider-in-authentik-for-cli).

3. Save the file as `authentik.reg` and ensure that **Save as type** is set to **All Files**.
4. Locate the `authentik.reg` file in File Explorer, right-click it and select **Merge**.
5. Approve the admin prompt.

## Logging

The authentik Agent primarily outputs logs to Windows Event Viewer.

WCP logs to the `wcp.log` located in `C:\Program Files\Authentik Security Inc\wcp`.
