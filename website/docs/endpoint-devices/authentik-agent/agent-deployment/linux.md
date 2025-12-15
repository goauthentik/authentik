---
title: Deploy authentik Agent on Linux
sidebar_label: Linux
tags: [authentik Agent, linux, deploy, packages]
---

## What it can do

- Retrieves information about the host and reports it to authentik, see [Device Compliance](../../device-compliance/index.mdx).
- Authorize Sudo elevation, see [Sudo authorization](../../device-authentication/sudo-authorization.md).
- SSH to Linux hosts using authentik credentials, see [SSH authentication](../../device-authentication/ssh-authentication.mdx).
- Authenticate CLI applications using authentik credentials, see [CLI application authentication](../../device-authentication/cli-app-authentication/index.mdx).

## Prerequisites

You must [configure your authentik deployment](../configuration.md) to support the authentik Agent.

## Install the authentik Agent on Linux

(TODO - guide via UI)

Follow these steps to install the authentik Agent on your Linux device:

1. Open a Terminal session and install the required GPG key:

```sh
curl -fsSL https://pkg.goauthentik.io/keys/gpg-key.asc | sudo gpg --dearmor -o /usr/share/keyrings/authentik-keyring.gpg
```

2. Add the repository:

```sh
echo "deb [signed-by=/usr/share/keyrings/authentik-keyring.gpg] https://pkg.goauthentik.io stable main" | sudo tee /etc/apt/sources.list.d/authentik.list
```

3. Update your repositories and install the authentik Agent packages:

```sh
sudo apt update
sudo apt install authentik-cli authentik-agent authentik-sysd
```

4. Confirm that the authentik Agent is installed:
```sh
ak
You should see a response that starts with: `authentik CLI v<version_number>`

## Enable device authentication

To enable [device authentication features](../../device-authentication/index.mdx), the device must be connected to an authentik deployment. To do so, follow these steps:

1. Open a Terminal session and run the following command:

```sh
ak config setup --authentik-url https://authentik.company
```

2. A browser will open and direct you to the authentik login page. Once authenticated, the authentik Agent will be configured.

## Enable device compliance and SSH access

To enable [device compliance features](../../device-compliance/index.mdx) and the device [accepting SSH connections](../../device-authentication/ssh-authentication.mdx), you must join the device to an authentik domain. This can be done via the CLI or by editing a configuration file.

### CLI

1. Open a Terminal session and run the following command:

```sh
ak-sysd domains join <deployment_name> --authentik-url https://authentik.company
```

- `deployment_name` is the name that will be used to identify the authentik deployment on the device.
- `https://authentik.company` is the fully qualified domain name of the authentik deployment.

2. (TODO)

### Configuration file

1. Create the following file: `/etc/authentik/domains/ak.json`
2. Paste the following values into the file:

(TODO) JSON codeblock

## Logging

authentik Agent logs are available via the system journal (`systemd`) or `syslog`, depending on the distribution.
