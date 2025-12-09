---
title: Deploy authentik Agent on Windows
sidebar_label: Windows
tags: [authentik Agent, windows]
---

## What does it do

- Retrieves information about the host for use in authentik, see [Device Compliace](../../device-compliance/index.mdx).
- SSH to Linux hosts using authentik credentials, see [SSH authentication](../../device-authentication/ssh-authentication.mdx).
- Authenticate CLI applications using authentik credentials, see [CLI application authentication](../../device-authentication/cli-app-authentication/index.mdx).

:::info Windows Versions
The authentik Agent is currently only tested on Windows 11 and Windows Server 2022.
:::

## Prerequisites

You must [configure your authentik deployment](../configuration.md) to support the authentik Agent.

## Install the authentik Agent

(TODO - guide via UI)

Follow these steps to install the authentik Agent on your Windows device:

1. Open the [authentik Platform Packages](https://pkg.goauthentik.io) page. (TODO - naming)
2. Under **Desktop packages** click on **Windows** to download the Windows MSI file.
3. Once the download is complete, install the MSI file.
4. _(Optional)_ During installation, select [Windows Credential Provider](<#Windows-Credential-Provider-(WCP)>) if you want to log in to the Windows device using authentik credentials.

5. Confirm that authentik Platform is installed by opening a Powershell or Terminal window and entering the following command: `ak`
   You should see a response that starts with: `authentik CLI v<version_number>`

## Configure the authentik Agent

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

#### Configure Windows Credential Provider

You'll need to add the following registry entry:

```
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\CLSID\{7BCC7941-18BA-4A8E-8E0A-1D0F8E73577A}]
"URL"="https://authentik.company"       ; authentik URL
"ClientID"="authentik-cli"              ; Client ID
```

## Logging

authentik Platform primarily outputs logs to Windows Event Viewer.

The Windows Credential Provider logs to the `wcp.log` file in `C:\Program Files\Authentik Security Inc\wcp`:
