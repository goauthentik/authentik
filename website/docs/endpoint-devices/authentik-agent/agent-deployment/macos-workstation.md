---
title: Deploy authentik Agent on a macOS workstation
sidebar_label: macOS workstation
---

## What does it do

- Allows you to SSH to Linux hosts using authentik credentials.
- Retrieves information about the host for use in authentik.
- Allows logging in to the device using authentik credentials.

## Install the authentik Agent

Follow these steps to install the authentik Agent on your macOS workstation:

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
