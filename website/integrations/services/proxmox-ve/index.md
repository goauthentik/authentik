---
title: Integrate with Proxmox VE
sidebar_label: Proxmox VE
---

# Integrate with Proxmox VE

<span class="badge badge--secondary">Support level: Community</span>

## What is Proxmox VE

> Proxmox Virtual Environment is an open source server virtualization management solution based on QEMU/KVM and LXC. You can manage virtual machines, containers, highly available clusters, storage, and networks with an integrated, easy-to-use web interface or via CLI. Proxmox VE code is licensed under the GNU Affero General Public License, version 3. The project is developed and maintained by Proxmox Server Solutions GmbH.
>
> -- https://pve.proxmox.com/wiki/Main_Page

:::caution
Requires Proxmox VE 7.0 or newer.
:::

## Preparation

The following placeholders are used in this guide:

- `proxmox.company` is the FQDN of the Proxmox VE server.
- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

1. In the Admin interface, navigate to **Applications -> Providers** to create an OAuth2/OpenID provider with these settings:

    - **Name:** proxmox
    - **Redirect URI:** `https://proxmox.company:8006` (No trailing slash, include the web interface port)
    - **Signing Key:** Select any available key

2. Create an application using the provider.
    - Under **Applications** > **Applications** in the Admin interface, create a new application and configure it to use the provider created in the previous step.
    - Optionally, apply access restrictions to the application.
    - Set the **Launch URL** to `https://proxmox.company:8006`.

## Proxmox VE configuration (using the web interface)

1. Log in to the Proxmox VE web interface using an administrative account.

2. Navigate to authentication source settings.

    - Go to **Datacenter** > **Permissions** > **Realms**.
    - Click **Add** and select **Realm** to open the Add Realm dialog.

3. Fill out the OpenID Connect settings.

    - In the dialog that appears, fill in the following details:
        - **Issuer URL**: Enter the Issuer URL from authentik (found in your provider's overview tab), e.g., `https://authentik.company/application/o/proxmox/`.
        - **Realm**: Enter a name for this authentication source, such as `authentik`.
        - **Client ID**: Enter the Client ID found on the provider overview page.
        - **Client Key**: Enter the Client Secret. (To find this value click **Edit** on the Provider overview page.)
        - **Username claim**: Set this to `username`.
        - **Autocreate users**: Check this box if you want Proxmox to automatically create users upon first login. If checked, users will appear in Proxmox with the format `<authentik username>@authentik`.
        - **Default**: Check this if you want OpenID Connect to be pre-selected as the default on the login screen.

    **Example configuration**:

    ![Proxmox Add OpenID Connect Server Dialog](proxmox-source.png)

4. **Save the configuration**.

    - Click **Add** to save the settings.

5. **Assign permissions**

    - After setting up the authentication source, go to **Permissions** to assign roles and permissions for each user as needed.

6. **Logging in**

    - Users can select this authentication method from the Proxmox login screen, or if set as default, it will be automatically selected.

    ![Proxmox login page with authentik marked as default login method](proxmox-login.png)

## Proxmox VE configuration (using CLI)

To configure OpenID Connect authentication via the CLI, SSH into any Proxmox cluster node and use the following command:

```bash
pveum realm add authentik --type openid --issuer-url https://authentik.company/application/o/proxmox/ --client-id xxx --client-key xxx --username-claim username --autocreate 1
```
