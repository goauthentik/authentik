---
title: Deploy authentik Agent on macOS
sidebar_label: macOS
tags: [authentik Agent, mac, macos, deploy]
---

## What does it do

- Retrieves information about the host for use in authentik, see [Device Compliace](../../device-compliance/index.mdx).
- Authorize Sudo elevation, see [Sudo authorization](../../device-authentication/sudo-authorization.md). (TODO - needs testing)
- SSH to Linux hosts using authentik credentials, see [SSH authentication](../../device-authentication/ssh-authentication.mdx).
- Authenticate CLI applications using authentik credentials, see [CLI application authentication](../../device-authentication/cli-app-authentication/index.mdx).

## Prerequisites

You must [configure your authentik deployment](../configuration.md) to support the authentik Agent.

## Install the authentik Agent

(TODO - guide via UI)

Follow these steps to install the authentik Agent on your macOS device:

1. Open the [authentik Platform Packages](https://pkg.goauthentik.io) page. (TODO)
2. Under **Desktop packages** click on **macOS** to download the macOS package.
3. Once the download is complete, attempt to install the package. Default Apple security settings should block the install.
   This can be avoided by Option + Right Clicking the package and clicking **Open**.
   Alternatively use the following command to remove the package from quarantine: `xattr -r -d com.apple.quarantine ~/Downloads/authentik\ agent\ installer.pkg`.
4. If prompted, enter your login password and click OK. You should now be able to install the package.
5. Continue through the installation wizard steps.
6. Confirm that the authentik Agent is installed by opening a Terminal window and entering the following command: `ak`
   You should see a response that starts with: `authentik CLI v<version_number>`

## Configure the authentik Agent

1. Open a Terminal session and run the following command:

```sh
ak config setup --authentik-url <authentik_FQDN>
```

2. A browser will open and direct you to the authentik login page. Once authenticated, the authentik Agent will be configured.

## Logging

The authentik Agent uses macOS's native logging abilities. To retrive the logs, open the Console application and then filter for the relevant authentik Agent component .e.g. `==sysd`.
