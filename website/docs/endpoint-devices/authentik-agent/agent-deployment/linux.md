---
title: Deploy authentik Agent on Linux
sidebar_label: Linux
tags: [authentik Agent, linux, deploy, packages]
---

## What does it do

- Retrieves information about the host for use in authentik, see [Device Compliace](../../device-compliance/index.mdx).
- Authorize Sudo elevation, see [Sudo authorization](../../device-authentication/sudo-authorization.md).
- SSH to Linux hosts using authentik credentials, see [SSH authentication](../../device-authentication/ssh-authentication.mdx).
- Authenticate CLI applications using authentik credentials, see [CLI application authentication](../../device-authentication/cli-app-authentication/index.mdx).

## Prerequisites

You must [configure your authentik deployment](../configuration.md) to support the authentik Agent.

## Install the authentik Agent in Linux

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

4. Confirm that the authentik Agent is installed by entering the following command: `ak`
   You should see a response that starts with: `authentik CLI v<version_number>`

## Configure the authentik Agent

1. Open a Terminal session and run the following command:

```sh
ak config setup --authentik-url <authentik_FQDN>
```

2. A browser will open and direct you to the authentik login page. Once authenticated, the authentik Agent will be configured.

## Logging

All authenik Agent related logs are outputted to the Linux system logging service, `syslog`.
