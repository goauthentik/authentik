---
title: Integrate with Proxmox VE
sidebar_label: Proxmox VE
---

# Proxmox VE

<span class="badge badge--secondary">Support level: Community</span>

## What is Proxmox VE

> Proxmox Virtual Environment is an open source server virtualization management solution based on QEMU/KVM and LXC. You can manage virtual machines, containers, highly available clusters, storage and networks with an integrated, easy-to-use web interface or via CLI. Proxmox VE code is licensed under the GNU Affero General Public License, version 3. The project is developed and maintained by Proxmox Server Solutions GmbH.
>
> -- https://pve.proxmox.com/wiki/Main_Page

:::caution
This requires Proxmox VE 7.0 or newer.
:::

## Preparation

The following placeholders will be used:

-   `proxmox.company` is the FQDN of the Proxmox VE server.
-   `authentik.company` is the FQDN of the authentik install.

## authentik Setup

1. **Navigate to the Admin Interface, then click Providers to create an OAuth2/OpenID provider with these settings:**
   - **Name:** proxmox
   - **Redirect URI:** `https://proxmox.company:8006` (Note the absence of the trailing slash, and the inclusion of the web interface port)
   - **Signing Key:** Select any available key

2. **Create an Application Using This Provider**
   - Under *Applications* >  *Applications* of the Admin interface, create a new application and configure it to use the provider created in the previous step.
   - Optionally, apply access restrictions to the application.
   - Set the **Launch URL** to `https://proxmox.company:8006`.

## Proxmox VE Setup (Web interface)

1. **Log in to the Proxmox Web Interface**
   - Access the Proxmox VE web interface and log in with an administrative account.

2. **Navigate to Authentication Source Settings**
   - Go to **Datacenter** > **Permissions** > **Realms**.
   - Click **Add** and select **Realm** to open the Add Realm dialog.

3. **Fill Out the OpenID Connect Settings**
   - In the dialog that appears, fill in the following details:
     - **Issuer URL**: Enter the Issuer URL from authentik (found under *Provider Metadata*), e.g., `https://authentik.company/application/o/proxmox/`.
     - **Realm**: Enter a name for this authentication source, such as `authentik`.
     - **Client ID**: Enter the Client ID found on the provider overview page.
     - **Client Key**: Enter the Client Secret found by clicking *Edit* on the Provider overview page.
     - **Username Claim**: Set this to `username`.
     - **Autocreate Users**: Check this box if you want Proxmox to automatically create users upon first login. If checked, users will appear in Proxmox with the format `<authentik username>@authentik`.
     - **Default**: Check this if you want OpenID Connect to be pre-selected as the default on the login screen.

   Here’s an example configuration:

   ![Proxmox Add OpenID Connect Server Dialog](proxmox-source.png)

4. **Save the Configuration**
   - Click **Add** to save the settings.

5. **Assign Permissions**
   - After setting up the authentication source, go to **Permissions** to assign roles and permissions for each user as needed. 

6. **Logging In**
   - Users can select this authentication method from the Proxmox login screen, or if set as default, it will be automatically selected.


## Proxmox VE Setup (CLI)

To configure OpenID Connect authentication via the CLI, SSH into any Proxmox cluster node and use the following command:

```bash
pveum realm add authentik --type openid --issuer-url https://authentik.company/application/o/proxmox/ --client-id xxx --client-key xxx --username-claim username --autocreate 1
```

You can find the Issuer URL on the Provider Metadata tab in authentik. You can find the Client ID and Key on the Provider Edit dialog in authentik.

After configuring the source in Proxmox, any user that logs in to Proxmox for the first time automatically gets an user named `<authentik username>@<pve realm name>`. In this example,
authentik user `bob` will get an user named `bob@authentik` in Proxmox. You can then assign Permissions as normally in Proxmox. You can also pre-create the users in Proxmox if you want
the user to be able to perform actions immediately after first login.

There is no way to directly trigger an OpenID Connect login in Proxmox, but if you set the source as 'default', it will be automatically selected on the Proxmox login screen.

![](proxmox-login.png)
