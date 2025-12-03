---
title: Deploy authentik Agent on a Windows workstation
sidebar_label: Windows workstation
---

## What does it do

- Allows you to SSH to Linux hosts using authentik credentials.
- Retrieves information about the host for use in authentik.
- Allows logging in to the device using authentik credentials. (optional)

:::info Windows 11 only
The authentik Agent is currently only supported on Windows 11.
:::

## Install the authentik Agent

Follow these steps to install the authentik Agent on your Windows workstation:

1. Open the [authentik Platform Packages](https://pkg.goauthentik.io) page. (TODO)
2. Under **Desktop packages** click on **Windows** to download the Windows MSI file.
3. Once the download is complete, install the MSI file.
4. _(Optional)_ During installation, select [Windows Credential Provider](<#Windows-Credential-Provider-(WCP)>) if you want to log in to the Windows device using authentik credentials.

5. Confirm that authentik Platform is installed by opening a Powershell or Terminal window and entering the following command: `ak`
   You should see a response that starts with: `authentik CLI v<version_number>`

## Configure Platform

1. Open a Terminal session and run the following command:

```sh
ak config setup --authentik-url <authentik_FQDN>
```

2. A browser will open and direct you to the authentik login page. Once authenticated, Platform will be configured.

## Windows Credential Provider (WCP)

Windows Credential Provider is a component of authentik Platform that allows logging in to Windows workstations using authentik credentials.

It currently only supports local login; RDP login is not supported.

:::warning

- When WCP is enabled, the password of the Windows user account that's used is set to a random string.
- WCP can cause issues with user encrypted directories.
- Support with Active directory has not been confirmed yet.
  :::

### authentik configuration

To support the deployment of Windows Credential Provider, you need to configure your authentik deployment. (TODO)

### Windows Credential Provider configuration

Now you'll need to configure Windows Credential Provider on the Windows device that you want to log in to.

#### Configure Windows Credential Provider

You'll need to add the following registry entry:

```
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\CLSID\{7BCC7941-18BA-4A8E-8E0A-1D0F8E73577A}]
"URL"="https://authentik.company"       ; authentik URL
"ClientID"="authentik-wcp"              ; Client ID
```

## Logging

authentik Platform primarily outputs logs to Windows Event Viewer.

The Windows Credential Provider logs to the `wcp.log` file in `C:\Program Files\Authentik Security Inc\wcp`:
