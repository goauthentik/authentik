---
title: Deploy authentik Agent on a Linux workstation
sidebar_label: Linux workstation
---

## What does it do

- Allows you to SSH to Linux hosts using authentik credentials.
- Retrieves information about the host for use in authentik.
- Allows logging in to the device using authentik credentials.

## Install the authentik Agent

Follow these steps to install the authentik Agent on your Linux workstation:

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
