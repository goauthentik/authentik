---
title: Sudo authorization
sidebar_label: Sudo authorization
tags: [sudo, authentik Agent]
---

You can use the [authentik Agent](../authentik-agent/index.mdx) to authorize sudo elevation on Linux endpoint devices.

When you run a sudo command on an endpoint device, you will either be prompted for your authentik credentials or, if you are already connected via [SSH using the authentik agent](./ssh-authentication.mdx), sudo will be authorized automatically.

## Prerequisites

- [authentik Agent needs to be deployed](../authentik-agent/agent-deployment/index.mdx) on the device.
- Sudo authorization needs to be configured on the device, see the [Configure sudo authorization on an endpoint device](#configure-sudo-authorization-on-an-endpoint-device) section below.

## How to authorize sudo on an endpoint device

- needs ak-agent, ak-sysd
- only with `ak ssh`
  (TODO)

## Configure sudo authorization on an endpoint device

If you want a Linux Endpoint Device to support authorizing using authentik credentials, you will need to install the `libpam-authentik` package in addition to the authentik Agent. This is a PAM Module, which provides token-based and interactive authentication via authentik.

Authorization is only possible if the Linux device is aware of the authentik user which is attempting to authorize. This can be achieved in one of two ways:

1. **Provision user accounts** - Create users on the Linux device with usernames that match authentik users that need to authorize sudo to the device. This can be done manually or via automation tools like Ansible.
2. **`libnss-authentik`** - This is a package that can be installed on the Linux device. It is an NSS module that makes the Linux device aware of authentik users. Similar to adding a Linux device to an Active Directory or LDAP domain.

### Install the `libpam-authentik` package _(required)_

:::info Prerequisites
You must have already deployed and configured the authentik Agent on the device.
:::

Run the following command to install the `libpam-authentik` package:

```sh
sudo apt install libpam-authentik
```

### Install the `libnss-authentik` package _(optional)_

Run the following command to install the `libnss-authentik` package:

```sh
sudo apt install libnss-authentik
```
