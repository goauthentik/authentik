---
title: Deploy authentik Agent on macOS
sidebar_label: macOS
tags: [authentik Agent, mac, macos, deploy]
---

## What it can do

- Retrieves information about the host for use in authentik, see [Device Compliance](../../device-compliance/index.mdx).
- Authorize Sudo elevation, see [Sudo authorization](../../device-authentication/sudo-authorization.md). (TODO - needs testing)
- SSH to Linux hosts using authentik credentials, see [SSH authentication](../../device-authentication/ssh-authentication.mdx).
- Authenticate CLI applications using authentik credentials, see [CLI application authentication](../../device-authentication/cli-app-authentication/index.mdx).

## Prerequisites

You must [configure your authentik deployment](../configuration.md) to support the authentik Agent.

## Install the authentik Agent

(TODO - guide via UI)

Follow these steps to install the authentik Agent on your macOS device:

1. Open the [authentik Platform Packages](https://pkg.goauthentik.io) page.
2. Under **Desktop packages** click on **macOS** to download the macOS package.
3. Once the download is complete, attempt to install the package. Default Apple security settings should block the install.
    - This can be avoided by Option + Right Clicking the package and clicking **Open**.
    - Alternatively use the following command to remove the package from quarantine: `xattr -r -d com.apple.quarantine "$HOME/Downloads/authentik agent installer.pkg"`
4. If prompted, enter your login password and click OK. You should now be able to install the package.
5. Continue through the installation wizard steps.
6. Confirm that the authentik Agent is installed by opening a Terminal window and entering the following command: `ak`
   You should see a response that starts with: `authentik CLI v<version_number>`

## Enable device authentication

To enable [device authentication features](../../device-authentication/index.mdx), you must connect the device to an authentik deployment. To do so, follow these steps:

1. Open a Terminal session and run the following command:

```sh
ak config setup --authentik-url <authentik_FQDN>
```

2. A browser will open and direct you to the authentik login page. Once authenticated, the authentik Agent will be configured.

## Enable device compliance

To enable [device compliance features](../../device-compliance/index.mdx), you must join the device to an authentik domain. This can be done via the CLI or by editing a configuration file.

### CLI

1. Open a Terminal session and run the following command:

```sh
ak-sysd domains join <name_for_authentik_domain> -a <authentik_FQDN>
```

- `name_for_authentik_domain` is the name that will be used to identify the authentik deployment on the device.
- `authentik_FQDN` is the fully qualified domain name of the authentik deployment.

2. (TODO)

### Configuration file

1. Create the following file: `/etc/authentik/domains/ak.json`
2. Paste the following values into the file:

(TODO) JSON codeblock

## Logging

The authentik Agent uses macOS's native logging abilities. To retrieve the logs, open the Console application and then filter for the relevant authentik Agent component (for example, `==sysd`).
