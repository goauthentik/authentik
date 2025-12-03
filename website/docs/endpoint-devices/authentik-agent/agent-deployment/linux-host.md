---
title: Deploy authentik Agent on a Linux host
sidebar_label: Linux host
---

## What does it do

- Allows you to SSH to the Linux host using authentik credentials from another device using the authentik Agent.
- Retrieves information about the host for use in authentik.

## authentik Agent components on Linux

### authentik-cli

Provides commands for interacting with authentik-agent.

### authentik-agent

User service.

### authentik-sysd

System service.

### libpam-authentik

PAM Module, which provides token-based and interactive authentication via authentik. Requires authentik-sysd running.

Authentication is only possible if Linux is aware of the authentik user, which can be achieved with [libnss-authentik](#libnss-authentik) or by manually creating user accounts that match the authentik users that need to authenticate.

### libnss-authentik

NSS Module. Requires authentik-sysd running.

Makes the Linux host aware of authentik users.

## authentik configuration

To support the deployment of the authentik Agent, you'll first need to [configure your authentik deployment](../agent-configuration.md).

## Host configuration

Now you'll need to install and configure the authentik Agent on the Linux host that you want to SSH to.

### Install the authentik Agent

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
    sudo apt install authentik-cli authentik-sysd libpam-authentik libnss-authentik
    ```

4. Confirm that the authentik Agent is installed by entering the following command: `ak`
   You should see a response that starts with: `authentik CLI v<version_number>`

### Configure the authentik Agent

(TODO) This section needs a rework

1. Open a Terminal session and run the following command:

    ```sh
    ak-sysd domains join <domain_name> -d <app_name_in_authentik> -a <authentik_FQDN>
    ```

- `<domain_name>` is a name for the authentik instance (e.g. `authentik-Prod`).
- `<app_name_in_authentik>` is the name of the application created in authentik (e.g. `authentik-pam`). (TODO)
- `<authentik_FQDN>` is the FQDN of your authentik instance.

2. You will be prompted for a token, enter the token that you previously created.
3. To confirm that the authentik Agent is configured correctly, run the `ak-sysd check` command. This outputs the status of all authentik Agent components.

## Logging

All authenik Agent related logs are outputted to the Linux system logging service, `syslog`.
